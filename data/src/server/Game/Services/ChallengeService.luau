--!strict

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

type GameState = "PREPARATION" | "STARTING" | "DEFENDING" | "VICTORY" | "DEFEAT" | "REVIEW"
type Outcome = "VICTORY" | "DEFEAT"
type StartAction = "Start" | "ReturnToPreparation"
type DefenseType = "Empty" | "Wall" | "Turret"
type DefenseSnapshot = { [string]: DefenseType }
type WaveConfig = {
	count: number,
	spawnIntervalSeconds: number,
}
type ChallengeConfigType = {
	countdownSeconds: number,
	intermissionSeconds: number,
	outcomeDisplaySeconds: number,
	coreDamagePerEnemy: number,
	interactionDistance: number,
	requestCooldownSeconds: number,
	waves: { WaveConfig },
}
type GameTypesModule = {
	isStartAction: (value: unknown) -> boolean,
}
type StateService = {
	getPhase: (self: StateService) -> GameState,
	setPhase: (self: StateService, phase: GameState) -> boolean,
	setCountdown: (self: StateService, secondsRemaining: number) -> (),
	setWave: (self: StateService, wave: number, totalWaves: number) -> (),
	restoreCore: (self: StateService) -> (),
	damageCore: (self: StateService, damage: number) -> number,
	setReachedCore: (self: StateService, count: number) -> (),
	setReview: (
		self: StateService,
		outcome: Outcome,
		firstDestroyed: string,
		reachedCore: number
	) -> (),
	clearReview: (self: StateService) -> (),
}
type BuildServiceContract = {
	setEnemyCallbacks: (
		self: BuildServiceContract,
		findNearestEnemy: (position: Vector3, range: number) -> Model?,
		damageEnemy: (enemy: Model, damage: number) -> ()
	) -> (),
	setDestroyedCallback: (
		self: BuildServiceContract,
		callback: (description: string) -> ()
	) -> (),
	setBuildEnabled: (self: BuildServiceContract, enabled: boolean) -> (),
	snapshot: (self: BuildServiceContract) -> DefenseSnapshot,
	restore: (self: BuildServiceContract, snapshot: DefenseSnapshot) -> (),
	findNearestWall: (self: BuildServiceContract, position: Vector3, range: number) -> Model?,
	damageWall: (self: BuildServiceContract, wall: Model, damage: number) -> boolean,
}
type EnemyServiceContract = {
	setCombatCallbacks: (
		self: EnemyServiceContract,
		findNearestWall: (position: Vector3, range: number) -> Model?,
		damageWall: (wall: Model, damage: number) -> boolean,
		reachedCore: () -> ()
	) -> (),
	spawn: (self: EnemyServiceContract) -> boolean,
	getActiveCount: (self: EnemyServiceContract) -> number,
	findNearestEnemy: (self: EnemyServiceContract, position: Vector3, range: number) -> Model?,
	damageEnemy: (self: EnemyServiceContract, enemy: Model, damage: number) -> boolean,
	clear: (self: EnemyServiceContract) -> (),
}

local runtimeRequire = require

local function loadModule(moduleInstance: Instance): unknown
	assert(
		moduleInstance:IsA("ModuleScript"),
		string.format("%s must be a ModuleScript", moduleInstance:GetFullName())
	)
	return runtimeRequire(moduleInstance)
end

local sharedGame = ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Game")
local configFolder = sharedGame:WaitForChild("Config")
local ChallengeConfig =
	loadModule(configFolder:WaitForChild("ChallengeConfig")) :: ChallengeConfigType
local GameTypes = loadModule(sharedGame:WaitForChild("GameTypes")) :: GameTypesModule

local ChallengeService = {}
ChallengeService.__index = ChallengeService

export type Service = typeof(setmetatable(
	{} :: {
		_stateService: StateService,
		_buildService: BuildServiceContract,
		_enemyService: EnemyServiceContract,
		_console: BasePart,
		_requestTimes: { [Player]: number },
		_runToken: number,
		_snapshot: DefenseSnapshot?,
		_firstDestroyed: string,
		_reachedCore: number,
	},
	ChallengeService
))

local function getPlayerRoot(player: Player): BasePart?
	local character = player.Character
	if not character then
		return nil
	end

	local root = character:FindFirstChild("HumanoidRootPart")
	if root and root:IsA("BasePart") then
		return root
	end

	return nil
end

function ChallengeService.new(
	prototype: Folder,
	requestStartChallenge: RemoteEvent,
	stateService: StateService,
	buildService: BuildServiceContract,
	enemyService: EnemyServiceContract
): Service
	local challengeConsole = prototype:FindFirstChild("ChallengeConsole")
	assert(
		challengeConsole and challengeConsole:IsA("BasePart"),
		"Prototype.ChallengeConsole is required"
	)

	local self: Service = setmetatable({
		_stateService = stateService,
		_buildService = buildService,
		_enemyService = enemyService,
		_console = challengeConsole,
		_requestTimes = {},
		_runToken = 0,
		_snapshot = nil,
		_firstDestroyed = "Aucune",
		_reachedCore = 0,
	}, ChallengeService)

	buildService:setEnemyCallbacks(function(position: Vector3, range: number): Model?
		return enemyService:findNearestEnemy(position, range)
	end, function(enemy: Model, damage: number)
		enemyService:damageEnemy(enemy, damage)
	end)

	buildService:setDestroyedCallback(function(description: string)
		self:_onStructureDestroyed(description)
	end)

	enemyService:setCombatCallbacks(function(position: Vector3, range: number): Model?
		return buildService:findNearestWall(position, range)
	end, function(wall: Model, damage: number): boolean
		return buildService:damageWall(wall, damage)
	end, function()
		self:_onEnemyReachedCore()
	end)

	requestStartChallenge.OnServerEvent:Connect(function(player: Player, action: unknown)
		self:_handleRequest(player, action)
	end)

	Players.PlayerRemoving:Connect(function(player: Player)
		self._requestTimes[player] = nil
	end)

	self:_setConsoleEnabled(true)
	return self
end

function ChallengeService._handleRequest(self: Service, player: Player, actionValue: unknown)
	if player.Parent ~= Players or not GameTypes.isStartAction(actionValue) then
		return
	end

	local now = os.clock()
	local previousRequest = self._requestTimes[player]
	if previousRequest and now - previousRequest < ChallengeConfig.requestCooldownSeconds then
		return
	end
	self._requestTimes[player] = now

	local action = actionValue :: StartAction
	if action == "ReturnToPreparation" then
		if self._stateService:getPhase() == "REVIEW" then
			self:_returnToPreparation()
		end
		return
	end

	if self._stateService:getPhase() ~= "PREPARATION" then
		return
	end

	local playerRoot = getPlayerRoot(player)
	if not playerRoot then
		return
	end
	if
		(playerRoot.Position - self._console.Position).Magnitude
		> ChallengeConfig.interactionDistance
	then
		return
	end

	self:_beginChallenge()
end

function ChallengeService._beginChallenge(self: Service)
	if self._stateService:getPhase() ~= "PREPARATION" then
		return
	end
	if not self._stateService:setPhase("STARTING") then
		return
	end

	self._runToken += 1
	local token = self._runToken
	self._snapshot = self._buildService:snapshot()
	self._firstDestroyed = "Aucune"
	self._reachedCore = 0
	self._enemyService:clear()
	self._stateService:clearReview()
	self._stateService:restoreCore()
	self._stateService:setWave(0, #ChallengeConfig.waves)
	self._buildService:setBuildEnabled(false)
	self:_setConsoleEnabled(false)

	task.spawn(function()
		self:_runChallenge(token)
	end)
end

function ChallengeService._runChallenge(self: Service, token: number)
	for secondsRemaining = ChallengeConfig.countdownSeconds, 1, -1 do
		if token ~= self._runToken or self._stateService:getPhase() ~= "STARTING" then
			return
		end
		self._stateService:setCountdown(secondsRemaining)
		task.wait(1)
	end

	if token ~= self._runToken or not self._stateService:setPhase("DEFENDING") then
		return
	end
	self._stateService:setCountdown(0)

	for waveIndex, wave in ChallengeConfig.waves do
		if token ~= self._runToken or self._stateService:getPhase() ~= "DEFENDING" then
			return
		end

		self._stateService:setWave(waveIndex, #ChallengeConfig.waves)
		for _ = 1, wave.count do
			if token ~= self._runToken or self._stateService:getPhase() ~= "DEFENDING" then
				return
			end
			self._enemyService:spawn()
			task.wait(wave.spawnIntervalSeconds)
		end

		if waveIndex < #ChallengeConfig.waves then
			task.wait(ChallengeConfig.intermissionSeconds)
		end
	end

	while
		token == self._runToken
		and self._stateService:getPhase() == "DEFENDING"
		and self._enemyService:getActiveCount() > 0
	do
		task.wait(0.25)
	end

	if token == self._runToken and self._stateService:getPhase() == "DEFENDING" then
		self:_finish("VICTORY")
	end
end

function ChallengeService._onStructureDestroyed(self: Service, description: string)
	if self._stateService:getPhase() == "DEFENDING" and self._firstDestroyed == "Aucune" then
		self._firstDestroyed = description
	end
end

function ChallengeService._onEnemyReachedCore(self: Service)
	if self._stateService:getPhase() ~= "DEFENDING" then
		return
	end

	self._reachedCore += 1
	self._stateService:setReachedCore(self._reachedCore)
	local coreHealth = self._stateService:damageCore(ChallengeConfig.coreDamagePerEnemy)
	if coreHealth <= 0 then
		self:_finish("DEFEAT")
	end
end

function ChallengeService._finish(self: Service, outcome: Outcome)
	if self._stateService:getPhase() ~= "DEFENDING" then
		return
	end
	if not self._stateService:setPhase(outcome) then
		return
	end

	self._runToken += 1
	self._enemyService:clear()
	self._buildService:setBuildEnabled(false)
	self:_setConsoleEnabled(false)
	self._stateService:setReview(outcome, self._firstDestroyed, self._reachedCore)

	task.delay(ChallengeConfig.outcomeDisplaySeconds, function()
		if self._stateService:getPhase() == outcome then
			self._stateService:setPhase("REVIEW")
		end
	end)
end

function ChallengeService._returnToPreparation(self: Service)
	if self._stateService:getPhase() ~= "REVIEW" then
		return
	end

	self._runToken += 1
	self._enemyService:clear()
	if self._snapshot then
		self._buildService:restore(self._snapshot)
	end
	self._stateService:restoreCore()
	self._stateService:clearReview()
	if not self._stateService:setPhase("PREPARATION") then
		return
	end
	self._buildService:setBuildEnabled(true)
	self:_setConsoleEnabled(true)
end

function ChallengeService._setConsoleEnabled(self: Service, enabled: boolean)
	local prompt = self._console:FindFirstChild("StartChallengePrompt")
	if prompt and prompt:IsA("ProximityPrompt") then
		prompt.Enabled = enabled
	end
end

return ChallengeService
