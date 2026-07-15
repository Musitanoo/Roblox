--!strict

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

type GameState = "PREPARATION" | "STARTING" | "DEFENDING" | "VICTORY" | "DEFEAT" | "REVIEW"
type Outcome = "VICTORY" | "DEFEAT"
type EnemyType = "Roamer" | "Brute"
type RouteId = "Left" | "Right"
type PieceType = "Wall" | "SlowTrap" | "Turret"
type BuildPieceData = {
	id: string,
	pieceType: PieceType,
	cellX: number,
	cellZ: number,
	rotation: number,
}
type DefenseSnapshot = {
	schemaVersion: number,
	revision: number,
	pieces: { [string]: BuildPieceData },
}
type ChallengeWave = {
	id: number,
	roamerCount: number,
	roamerIntervalSeconds: number,
	fixedLeftRoamers: number,
	fixedRightRoamers: number,
	bruteCount: number,
	restSeconds: number,
}
type ChallengeConfigType = {
	challengeId: string,
	countdownSeconds: number,
	bruteWarningSeconds: number,
	outcomeDisplaySeconds: number,
	interactionDistance: number,
	requestCooldownSeconds: number,
	waves: { ChallengeWave },
}
type StateService = {
	getPhase: (self: StateService) -> GameState,
	setPhase: (self: StateService, phase: GameState) -> boolean,
	restoreCore: (self: StateService) -> (),
	getCoreHealth: (self: StateService) -> number,
	setCountdown: (self: StateService, seconds: number) -> (),
	setWave: (self: StateService, wave: number, total: number) -> (),
	setBruteWarning: (self: StateService, message: string) -> (),
	clearTransient: (self: StateService) -> (),
}
type BuildService = {
	snapshot: (self: BuildService) -> DefenseSnapshot,
	restore: (self: BuildService, snapshot: DefenseSnapshot) -> (),
	setBuildEnabled: (self: BuildService, enabled: boolean) -> (),
}
type RouteService = {
	chooseRoamerRoute: (self: RouteService) -> RouteId,
	chooseBruteRoute: (self: RouteService) -> RouteId,
	chooseWaveThreeBruteRoutes: (self: RouteService) -> { RouteId },
	hideReviewMarkers: (self: RouteService) -> (),
	showReviewMarkers: (self: RouteService, report: ReviewReport) -> (),
}
type EnemyService = {
	spawn: (self: EnemyService, enemyType: EnemyType, routeId: RouteId) -> boolean,
	getActiveCount: (self: EnemyService) -> number,
	clear: (self: EnemyService) -> (),
	setCoreReachedCallback: (
		self: EnemyService,
		callback: (routeId: RouteId, healthRemaining: number) -> ()
	) -> (),
}
type StatsService = {
	begin: (self: StatsService, challengeId: string) -> (),
	finish: (self: StatsService, outcome: Outcome, coreHealth: number) -> ReviewReport,
	clear: (self: StatsService) -> (),
}
type ReviewReport = {
	LeftLaneEnemyCount: number,
	RightLaneEnemyCount: number,
	FirstBreachLane: string,
	FirstBreachPadId: string,
}

local runtimeRequire = require
local configFolder =
	ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Game"):WaitForChild("Config")
local ChallengeConfig =
	runtimeRequire(configFolder:WaitForChild("ChallengeConfig") :: ModuleScript) :: ChallengeConfigType

local ChallengeService = {}
ChallengeService.__index = ChallengeService

export type Service = typeof(setmetatable(
	{} :: {
		_console: BasePart,
		_requestStart: RemoteEvent,
		_requestReturn: RemoteEvent,
		_stateService: StateService,
		_buildService: BuildService,
		_routeService: RouteService,
		_enemyService: EnemyService,
		_statsService: StatsService,
		_snapshot: DefenseSnapshot?,
		_runToken: number,
		_transitioning: boolean,
		_finishing: boolean,
		_requestTimes: { [Player]: number },
	},
	ChallengeService
))

local function getPlayerRoot(player: Player): BasePart?
	local character = player.Character
	if not character then
		return nil
	end
	local root = character:FindFirstChild("HumanoidRootPart")
	return if root and root:IsA("BasePart") then root else nil
end

local function routeDisplay(routeId: RouteId): string
	return if routeId == "Left" then "GAUCHE" else "DROITE"
end

function ChallengeService.new(
	prototype: Folder,
	requestStart: RemoteEvent,
	requestReturn: RemoteEvent,
	stateService: StateService,
	buildService: BuildService,
	routeService: RouteService,
	enemyService: EnemyService,
	statsService: StatsService
): Service
	local console = prototype:FindFirstChild("ChallengeConsole")
	assert(console and console:IsA("BasePart"), "Prototype.ChallengeConsole is required")
	local self: Service = setmetatable({
		_console = console,
		_requestStart = requestStart,
		_requestReturn = requestReturn,
		_stateService = stateService,
		_buildService = buildService,
		_routeService = routeService,
		_enemyService = enemyService,
		_statsService = statsService,
		_snapshot = nil,
		_runToken = 0,
		_transitioning = false,
		_finishing = false,
		_requestTimes = {},
	}, ChallengeService)

	requestStart.OnServerEvent:Connect(function(player: Player)
		self:_handleStartRequest(player)
	end)
	requestReturn.OnServerEvent:Connect(function(player: Player)
		self:_handleReturnRequest(player)
	end)
	Players.PlayerRemoving:Connect(function(player: Player)
		self._requestTimes[player] = nil
	end)
	enemyService:setCoreReachedCallback(function(_routeId: RouteId, healthRemaining: number)
		if healthRemaining <= 0 then
			self:_finish("DEFEAT")
		end
	end)
	buildService:setBuildEnabled(true)
	return self
end

function ChallengeService._reply(
	remote: RemoteEvent,
	player: Player,
	accepted: boolean,
	message: string
)
	remote:FireClient(player, accepted, string.sub(message, 1, 64))
end

function ChallengeService._rateLimited(self: Service, player: Player): boolean
	local now = os.clock()
	local previous = self._requestTimes[player]
	self._requestTimes[player] = now
	return previous ~= nil and now - previous < ChallengeConfig.requestCooldownSeconds
end

function ChallengeService._handleStartRequest(self: Service, player: Player)
	if player.Parent ~= Players or self:_rateLimited(player) then
		return
	end
	if self._transitioning or self._finishing or self._stateService:getPhase() ~= "PREPARATION" then
		ChallengeService._reply(self._requestStart, player, false, "Challenge déjà en cours")
		return
	end
	local root = getPlayerRoot(player)
	if
		not root
		or (root.Position - self._console.Position).Magnitude
			> ChallengeConfig.interactionDistance
	then
		ChallengeService._reply(self._requestStart, player, false, "Approchez-vous de la console")
		return
	end

	self:_start()
	ChallengeService._reply(self._requestStart, player, true, "Challenge lancé")
end

function ChallengeService._handleReturnRequest(self: Service, player: Player)
	if player.Parent ~= Players or self:_rateLimited(player) then
		return
	end
	if self._transitioning or self._finishing or self._stateService:getPhase() ~= "REVIEW" then
		ChallengeService._reply(self._requestReturn, player, false, "Autopsie indisponible")
		return
	end
	self:_returnToPreparation()
	ChallengeService._reply(self._requestReturn, player, true, "Base modifiable")
end

function ChallengeService._start(self: Service)
	self._transitioning = true
	self._runToken += 1
	local token = self._runToken
	local snapshot = self._buildService:snapshot()
	self._snapshot = snapshot
	self._buildService:setBuildEnabled(false)
	self._routeService:hideReviewMarkers()
	self._enemyService:clear()
	self._statsService:begin(ChallengeConfig.challengeId)
	self._stateService:clearTransient()
	self._stateService:restoreCore()
	self._buildService:restore(snapshot)
	assert(self._stateService:setPhase("STARTING"), "PREPARATION to STARTING failed")
	self._transitioning = false
	task.spawn(function()
		self:_run(token)
	end)
end

function ChallengeService._wait(self: Service, seconds: number, token: number): boolean
	local deadline = os.clock() + math.max(0, seconds)
	repeat
		if token ~= self._runToken then
			return false
		end
		task.wait(math.min(0.1, math.max(0, deadline - os.clock())))
	until os.clock() >= deadline
	return token == self._runToken
end

function ChallengeService._run(self: Service, token: number)
	for seconds = ChallengeConfig.countdownSeconds, 1, -1 do
		self._stateService:setCountdown(seconds)
		if not self:_wait(1, token) then
			return
		end
	end
	self._stateService:setCountdown(0)
	if token ~= self._runToken or not self._stateService:setPhase("DEFENDING") then
		return
	end

	local totalWaves = #ChallengeConfig.waves
	for _, wave in ChallengeConfig.waves do
		if not self:_runWave(wave, totalWaves, token) then
			return
		end
	end
	if token == self._runToken and self._stateService:getPhase() == "DEFENDING" then
		self:_finish("VICTORY")
	end
end

function ChallengeService._announceAndSpawnBrutes(
	self: Service,
	wave: ChallengeWave,
	token: number
): boolean
	if wave.bruteCount <= 0 then
		return true
	end
	local routes: { RouteId }
	if wave.bruteCount == 2 then
		routes = self._routeService:chooseWaveThreeBruteRoutes()
	else
		routes = { self._routeService:chooseBruteRoute() }
	end
	local routeNames = routeDisplay(routes[1])
	if routes[2] then
		routeNames ..= " + " .. routeDisplay(routes[2])
	end
	self._stateService:setBruteWarning(
		string.format(
			"BRUTE ANNONCÉE • %s • %d s",
			routeNames,
			ChallengeConfig.bruteWarningSeconds
		)
	)
	if not self:_wait(ChallengeConfig.bruteWarningSeconds, token) then
		return false
	end
	self._stateService:setBruteWarning("")
	for index = 1, wave.bruteCount do
		if not self._enemyService:spawn("Brute", routes[index]) then
			return false
		end
	end
	return true
end

function ChallengeService._roamerRoute(self: Service, wave: ChallengeWave, index: number): RouteId
	if wave.fixedLeftRoamers > 0 or wave.fixedRightRoamers > 0 then
		if index % 2 == 1 and math.ceil(index / 2) <= wave.fixedLeftRoamers then
			return "Left"
		end
		return "Right"
	end
	return self._routeService:chooseRoamerRoute()
end

function ChallengeService._runWave(
	self: Service,
	wave: ChallengeWave,
	totalWaves: number,
	token: number
): boolean
	self._stateService:setWave(wave.id, totalWaves)
	if not self:_announceAndSpawnBrutes(wave, token) then
		return false
	end
	for index = 1, wave.roamerCount do
		if token ~= self._runToken or self._stateService:getPhase() ~= "DEFENDING" then
			return false
		end
		if not self._enemyService:spawn("Roamer", self:_roamerRoute(wave, index)) then
			return false
		end
		if index < wave.roamerCount and not self:_wait(wave.roamerIntervalSeconds, token) then
			return false
		end
	end
	if wave.id == totalWaves then
		while self._enemyService:getActiveCount() > 0 do
			if token ~= self._runToken or self._stateService:getPhase() ~= "DEFENDING" then
				return false
			end
			if not self:_wait(0.25, token) then
				return false
			end
		end
	end
	return wave.restSeconds <= 0 or self:_wait(wave.restSeconds, token)
end

function ChallengeService._finish(self: Service, outcome: Outcome)
	if self._finishing or self._stateService:getPhase() ~= "DEFENDING" then
		return
	end
	self._finishing = true
	self._runToken += 1
	local token = self._runToken
	assert(self._stateService:setPhase(outcome), "DEFENDING to outcome failed")
	self._stateService:setBruteWarning("")
	self._enemyService:clear()
	local report = self._statsService:finish(outcome, self._stateService:getCoreHealth())
	self._routeService:showReviewMarkers(report)
	task.spawn(function()
		self:_wait(ChallengeConfig.outcomeDisplaySeconds, token)
		if token == self._runToken and self._stateService:getPhase() == outcome then
			assert(self._stateService:setPhase("REVIEW"), "Outcome to REVIEW failed")
		end
		self._finishing = false
	end)
end

function ChallengeService._returnToPreparation(self: Service)
	self._transitioning = true
	self._runToken += 1
	self._enemyService:clear()
	local snapshot = self._snapshot
	if snapshot then
		self._buildService:restore(snapshot)
	end
	self._stateService:restoreCore()
	self._stateService:clearTransient()
	self._routeService:hideReviewMarkers()
	self._statsService:clear()
	assert(self._stateService:setPhase("PREPARATION"), "REVIEW to PREPARATION failed")
	self._buildService:setBuildEnabled(true)
	self._transitioning = false
end

return ChallengeService
