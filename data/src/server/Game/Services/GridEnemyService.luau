--!strict

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

type GameState = "PREPARATION" | "STARTING" | "DEFENDING" | "VICTORY" | "DEFEAT" | "REVIEW"
type EnemyType = "Roamer" | "Brute"
type RouteId = "Left" | "Right"
type TargetScore = {
	progress: number,
	coreDamage: number,
	spawnSerial: number,
}
type StateService = {
	getPhase: (self: StateService) -> GameState,
	damageCore: (self: StateService, number) -> number,
	setEnemiesRemaining: (self: StateService, number) -> (),
}
type RouteService = {
	getSpawn: (self: RouteService, RouteId) -> BasePart,
	getPath: (self: RouteService, RouteId, EnemyType) -> ({ Vector3 }, { string }),
}
type DefenseService = {
	findBlockingWall: (self: DefenseService, { string }, number, Vector3, number) -> Model?,
	damageWall: (self: DefenseService, Model, number, EnemyType, RouteId) -> boolean,
}
type StatsService = {
	recordEnemySpawn: (self: StatsService, RouteId) -> (),
	recordCoreHit: (self: StatsService, RouteId) -> (),
}
type EnemyTuning =
	{ maxHealth: number, moveSpeed: number, coreDamage: number, structureDPS: number }
type EnemyConfigType = {
	maxActiveEnemies: number,
	wallDetectionRange: number,
	arrivalDistance: number,
	roamer: EnemyTuning,
	brute: EnemyTuning,
}
type CombatRoutingPolicyModule = {
	IsHigherPriorityTarget: (TargetScore, TargetScore?) -> boolean,
}
type EnemyRecord = {
	model: Model,
	root: BasePart,
	enemyType: EnemyType,
	routeId: RouteId,
	points: { Vector3 },
	pathCellKeys: { string },
	pointIndex: number,
	spawnSerial: number,
	routeDistance: number,
	distanceTravelled: number,
	health: number,
	moveSpeed: number,
	coreDamage: number,
	structureDPS: number,
	slowMultiplier: number,
	slowUntil: number,
	wasEverSlowed: boolean,
}
type CoreReachedCallback = (RouteId, number) -> ()

local config = ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Game"):WaitForChild("Config")
local EnemyConfig = require(config:WaitForChild("EnemyConfig") :: ModuleScript) :: EnemyConfigType
local servicesFolder = script.Parent
assert(
	servicesFolder and servicesFolder:IsA("Folder"),
	"GridEnemyService must be under Game.Services"
)
local gameFolder = servicesFolder.Parent
assert(gameFolder and gameFolder:IsA("Folder"), "Game.Services must be under Game")
local CombatRoutingPolicy =
	require(gameFolder:WaitForChild("CombatRoutingPolicy") :: ModuleScript) :: CombatRoutingPolicyModule

local GridEnemyService = {}
GridEnemyService.__index = GridEnemyService

export type Service = typeof(setmetatable(
	{} :: {
		_stateService: StateService,
		_routeService: RouteService,
		_statsService: StatsService,
		_templates: { Roamer: Model, Brute: Model },
		_core: BasePart,
		_runtimeEnemies: Folder,
		_active: { [Model]: EnemyRecord },
		_spawnSerial: number,
		_defenseService: DefenseService?,
		_coreReachedCallback: CoreReachedCallback?,
		_heartbeatConnection: RBXScriptConnection?,
	},
	GridEnemyService
))

local function findOrCreateFolder(parent: Instance, name: string): Folder
	local existing = parent:FindFirstChild(name)
	if existing then
		assert(existing:IsA("Folder"), existing:GetFullName() .. " must be a Folder")
		return existing
	end
	local folder = Instance.new("Folder")
	folder.Name = name
	folder.Parent = parent
	return folder
end

local function planarDistance(left: Vector3, right: Vector3): number
	local deltaX = right.X - left.X
	local deltaZ = right.Z - left.Z
	return math.sqrt(deltaX * deltaX + deltaZ * deltaZ)
end

local function calculateRouteDistance(
	spawnPosition: Vector3,
	points: { Vector3 },
	corePosition: Vector3
): number
	local distance = 0
	local previous = spawnPosition
	for _, point in points do
		distance += planarDistance(previous, point)
		previous = point
	end
	return distance + planarDistance(previous, corePosition)
end

function GridEnemyService.new(
	prototype: Folder,
	templates: Folder,
	stateService: StateService,
	routeService: RouteService,
	statsService: StatsService
): Service
	local core = prototype:FindFirstChild("ObjectiveCore")
	local roamer = templates:FindFirstChild("BasicZombie")
	local brute = templates:FindFirstChild("Brute")
	assert(core and core:IsA("BasePart"), "Prototype.ObjectiveCore is required")
	assert(roamer and roamer:IsA("Model") and roamer.PrimaryPart, "BasicZombie template is invalid")
	assert(brute and brute:IsA("Model") and brute.PrimaryPart, "Brute template is invalid")
	local runtime = findOrCreateFolder(prototype, "Runtime")
	local runtimeEnemies = findOrCreateFolder(runtime, "Enemies")
	for _, child in runtimeEnemies:GetChildren() do
		child:Destroy()
	end
	local self: Service = setmetatable({
		_stateService = stateService,
		_routeService = routeService,
		_statsService = statsService,
		_templates = { Roamer = roamer, Brute = brute },
		_core = core,
		_runtimeEnemies = runtimeEnemies,
		_active = {},
		_spawnSerial = 0,
		_defenseService = nil,
		_coreReachedCallback = nil,
		_heartbeatConnection = nil,
	}, GridEnemyService)
	self._heartbeatConnection = RunService.Heartbeat:Connect(function(deltaTime: number)
		self:_update(math.min(deltaTime, 0.1))
	end)
	return self
end

function GridEnemyService.setDefenseService(self: Service, defenseService: DefenseService)
	self._defenseService = defenseService
end

function GridEnemyService.setCoreReachedCallback(self: Service, callback: CoreReachedCallback)
	self._coreReachedCallback = callback
end

function GridEnemyService.spawn(self: Service, enemyType: EnemyType, routeId: RouteId): boolean
	if
		self._stateService:getPhase() ~= "DEFENDING"
		or self:getActiveCount() >= EnemyConfig.maxActiveEnemies
	then
		return false
	end
	local tuning = if enemyType == "Brute" then EnemyConfig.brute else EnemyConfig.roamer
	local template = self._templates[enemyType]
	local spawnPart = self._routeService:getSpawn(routeId)
	local points, pathCellKeys = self._routeService:getPath(routeId, enemyType)
	if #points == 0 then
		return false
	end
	local model = template:Clone()
	local root = model.PrimaryPart
	assert(root, "Enemy template requires PrimaryPart")
	self._spawnSerial += 1
	model.Name = string.format("%s_%03d", enemyType, self._spawnSerial)
	model:SetAttribute("EnemyType", enemyType)
	model:SetAttribute("RouteId", routeId)
	model:SetAttribute("MaxHealth", tuning.maxHealth)
	model:SetAttribute("Health", tuning.maxHealth)
	model:SetAttribute("SlowMultiplier", 1)
	local y = spawnPart.Position.Y + model:GetExtentsSize().Y * 0.5
	model:PivotTo(CFrame.new(spawnPart.Position.X, y, spawnPart.Position.Z))
	model.Parent = self._runtimeEnemies
	self._active[model] = {
		model = model,
		root = root,
		enemyType = enemyType,
		routeId = routeId,
		points = points,
		pathCellKeys = pathCellKeys,
		pointIndex = 1,
		spawnSerial = self._spawnSerial,
		routeDistance = calculateRouteDistance(spawnPart.Position, points, self._core.Position),
		distanceTravelled = 0,
		health = tuning.maxHealth,
		moveSpeed = tuning.moveSpeed,
		coreDamage = tuning.coreDamage,
		structureDPS = tuning.structureDPS,
		slowMultiplier = 1,
		slowUntil = 0,
		wasEverSlowed = false,
	}
	self._statsService:recordEnemySpawn(routeId)
	self._stateService:setEnemiesRemaining(self:getActiveCount())
	return true
end

function GridEnemyService.getActiveCount(self: Service): number
	local count = 0
	for _ in self._active do
		count += 1
	end
	return count
end

function GridEnemyService.findPriorityEnemy(self: Service, position: Vector3, range: number): Model?
	local selected: Model? = nil
	local selectedScore: TargetScore? = nil
	for model, record in self._active do
		if
			model.Parent
			and record.health > 0
			and (record.root.Position - position).Magnitude <= range
		then
			local score: TargetScore = {
				progress = if record.routeDistance > 0
					then math.clamp(record.distanceTravelled / record.routeDistance, 0, 1)
					else 0,
				coreDamage = record.coreDamage,
				spawnSerial = record.spawnSerial,
			}
			if CombatRoutingPolicy.IsHigherPriorityTarget(score, selectedScore) then
				selected = model
				selectedScore = score
			end
		end
	end
	return selected
end

function GridEnemyService.damageEnemy(self: Service, enemy: Model, damage: number): number
	local record = self._active[enemy]
	if not record or record.health <= 0 then
		return 0
	end
	local actual = math.min(record.health, math.max(0, damage))
	record.health -= actual
	enemy:SetAttribute("Health", record.health)
	if record.health <= 0 then
		self:_remove(record)
	end
	return actual
end

function GridEnemyService.applySlowInRadius(
	self: Service,
	position: Vector3,
	radius: number,
	multiplier: number,
	durationSeconds: number
): number
	local newlyAffected = 0
	local now = os.clock()
	for _, record in self._active do
		if record.health > 0 and (record.root.Position - position).Magnitude <= radius then
			record.slowMultiplier = math.min(record.slowMultiplier, math.clamp(multiplier, 0.1, 1))
			record.slowUntil = math.max(record.slowUntil, now + math.max(0, durationSeconds))
			record.model:SetAttribute("SlowMultiplier", record.slowMultiplier)
			if not record.wasEverSlowed then
				record.wasEverSlowed = true
				newlyAffected += 1
			end
		end
	end
	return newlyAffected
end

function GridEnemyService.clear(self: Service)
	for _, child in self._runtimeEnemies:GetChildren() do
		child:Destroy()
	end
	table.clear(self._active)
	self._stateService:setEnemiesRemaining(0)
end

function GridEnemyService._remove(self: Service, record: EnemyRecord)
	self._active[record.model] = nil
	record.model:Destroy()
	self._stateService:setEnemiesRemaining(self:getActiveCount())
end

function GridEnemyService._reachCore(self: Service, record: EnemyRecord)
	local health = self._stateService:damageCore(record.coreDamage)
	self._statsService:recordCoreHit(record.routeId)
	self:_remove(record)
	if self._coreReachedCallback then
		self._coreReachedCallback(record.routeId, health)
	end
end

function GridEnemyService._update(self: Service, deltaTime: number)
	if self._stateService:getPhase() ~= "DEFENDING" then
		return
	end
	local now = os.clock()
	for model, record in self._active do
		if not model.Parent then
			self._active[model] = nil
			continue
		end
		local defenseService = self._defenseService
		local wall = if defenseService
			then defenseService:findBlockingWall(
				record.pathCellKeys,
				record.pointIndex,
				record.root.Position,
				EnemyConfig.wallDetectionRange
			)
			else nil
		if wall and defenseService then
			defenseService:damageWall(
				wall,
				record.structureDPS * deltaTime,
				record.enemyType,
				record.routeId
			)
			continue
		end
		if now >= record.slowUntil then
			record.slowMultiplier = 1
			record.model:SetAttribute("SlowMultiplier", 1)
		end
		local point = record.points[record.pointIndex]
		local target = if point
			then Vector3.new(point.X, record.root.Position.Y, point.Z)
			else Vector3.new(
				self._core.Position.X,
				record.root.Position.Y,
				self._core.Position.Z
			)
		local offset = target - record.root.Position
		local distance = offset.Magnitude
		if distance <= EnemyConfig.arrivalDistance then
			if point then
				record.pointIndex += 1
			else
				self:_reachCore(record)
			end
			continue
		end
		local movement = math.min(distance, record.moveSpeed * record.slowMultiplier * deltaTime)
		local nextPosition = record.root.Position + offset.Unit * movement
		record.distanceTravelled =
			math.min(record.routeDistance, record.distanceTravelled + movement)
		record.model:PivotTo(
			CFrame.lookAt(nextPosition, Vector3.new(target.X, nextPosition.Y, target.Z))
		)
	end
end

return GridEnemyService
