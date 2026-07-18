--!strict

local Debris = game:GetService("Debris")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

type GameState = "PREPARATION" | "STARTING" | "DEFENDING" | "VICTORY" | "DEFEAT" | "REVIEW"
type PieceType = "Wall" | "SlowTrap" | "Turret"
type EnemyType = "Roamer" | "Brute"
type RouteId = "Left" | "Right"
type BuildPieceData = {
	id: string,
	pieceType: PieceType,
	cellX: number,
	cellZ: number,
	rotation: number,
}
type BuildPlan = { schemaVersion: number, revision: number, pieces: { [string]: BuildPieceData } }
type Cell = { x: number, z: number }
type RouteDefenseState = {
	wallCount: number,
	wallHealth: number,
	slowTrapCount: number,
}
type StateService = { getPhase: (self: StateService) -> GameState }
type EnemyService = {
	findPriorityEnemy: (self: EnemyService, position: Vector3, range: number) -> Model?,
	damageEnemy: (self: EnemyService, enemy: Model, damage: number) -> number,
	applySlowInRadius: (self: EnemyService, Vector3, number, number, number) -> number,
}
type StatsService = {
	recordWallDamage: (self: StatsService, number) -> (),
	recordTurretDamage: (self: StatsService, number) -> (),
	recordEnemiesSlowed: (self: StatsService, number) -> (),
	recordFirstBreach: (self: StatsService, RouteId, string, EnemyType) -> boolean,
	recordWallDestroyed: (self: StatsService, string, EnemyType) -> (),
}
type DefenseConfigType = {
	slowTrap: {
		slowMultiplier: number,
		effectDurationSeconds: number,
		effectRadius: number,
	},
	turret: { range: number, damage: number, cooldownSeconds: number },
}
type PieceTuning = { maxHealth: number }
type GridConfig = {
	schemaVersion: number,
	width: number,
	cellSize: number,
}
type GridMathModule = {
	CellKey: (number, number) -> string,
	GetOccupiedCells: (BuildPieceData) -> { Cell },
}
type CombatRoutingPolicyModule = {
	FirstBlockingWallId: ({ string }, number, { [string]: string }, number) -> string?,
}
type DefenseRecord = {
	model: Model,
	piece: BuildPieceData,
	routeId: RouteId,
	occupiedCells: { Cell },
	health: number,
	nextShotAt: number,
}

local sharedGame = ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Game")
local config = sharedGame:WaitForChild("Config")
local BuildGridConfig =
	require(config:WaitForChild("BuildGridConfig") :: ModuleScript) :: GridConfig
local DefenseConfig =
	require(config:WaitForChild("DefenseConfig") :: ModuleScript) :: DefenseConfigType
local GridMath = require(sharedGame:WaitForChild("GridMath") :: ModuleScript) :: GridMathModule
local PieceConfig =
	require(config:WaitForChild("PieceConfig") :: ModuleScript) :: { [PieceType]: PieceTuning }
local servicesFolder = script.Parent
assert(
	servicesFolder and servicesFolder:IsA("Folder"),
	"GridDefenseService must be under Game.Services"
)
local gameFolder = servicesFolder.Parent
assert(gameFolder and gameFolder:IsA("Folder"), "Game.Services must be under Game")
local CombatRoutingPolicy =
	require(gameFolder:WaitForChild("CombatRoutingPolicy") :: ModuleScript) :: CombatRoutingPolicyModule

local GridDefenseService = {}
GridDefenseService.__index = GridDefenseService

export type Service = typeof(setmetatable(
	{} :: {
		_stateService: StateService,
		_statsService: StatsService,
		_runtimeDefenses: Folder,
		_records: { [string]: DefenseRecord },
		_byModel: { [Model]: DefenseRecord },
		_wallIdByCell: { [string]: string },
		_schemaVersion: number,
		_revision: number,
		_enemyService: EnemyService?,
		_trapElapsed: number,
		_heartbeatConnection: RBXScriptConnection?,
	},
	GridDefenseService
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

local function showTracer(parent: Instance, origin: Vector3, target: Vector3)
	local offset = target - origin
	if offset.Magnitude <= 0.1 then
		return
	end
	local tracer = Instance.new("Part")
	tracer.Name = "TurretTracer"
	tracer.Anchored = true
	tracer.CanCollide = false
	tracer.CanQuery = false
	tracer.CanTouch = false
	tracer.Material = Enum.Material.Neon
	tracer.Color = Color3.fromRGB(90, 220, 255)
	tracer.Size = Vector3.new(0.14, 0.14, offset.Magnitude)
	tracer.CFrame = CFrame.lookAt(origin, target) * CFrame.new(0, 0, -offset.Magnitude * 0.5)
	tracer.Parent = parent
	Debris:AddItem(tracer, 0.08)
end

function GridDefenseService.new(
	prototype: Folder,
	stateService: StateService,
	statsService: StatsService
): Service
	local runtime = findOrCreateFolder(prototype, "Runtime")
	local runtimeDefenses = findOrCreateFolder(runtime, "Defenses")
	local self: Service = setmetatable({
		_stateService = stateService,
		_statsService = statsService,
		_runtimeDefenses = runtimeDefenses,
		_records = {},
		_byModel = {},
		_wallIdByCell = {},
		_schemaVersion = BuildGridConfig.schemaVersion,
		_revision = 0,
		_enemyService = nil,
		_trapElapsed = 0,
		_heartbeatConnection = nil,
	}, GridDefenseService)
	self._heartbeatConnection = RunService.Heartbeat:Connect(function(deltaTime: number)
		self:_update(math.min(deltaTime, 0.1))
	end)
	return self
end

function GridDefenseService.setEnemyService(self: Service, enemyService: EnemyService)
	self._enemyService = enemyService
end

function GridDefenseService.syncPlan(self: Service, plan: BuildPlan)
	table.clear(self._records)
	table.clear(self._byModel)
	table.clear(self._wallIdByCell)
	self._schemaVersion = plan.schemaVersion
	self._revision = plan.revision
	for id, piece in plan.pieces do
		local model: Model? = nil
		for _, candidate in self._runtimeDefenses:GetChildren() do
			if candidate:IsA("Model") and candidate:GetAttribute("PieceId") == id then
				model = candidate
				break
			end
		end
		if model and model:IsA("Model") then
			local maximum = PieceConfig[piece.pieceType].maxHealth
			model:SetAttribute("Health", maximum)
			model:SetAttribute("MaxHealth", maximum)
			local occupiedCells = GridMath.GetOccupiedCells(piece)
			local record: DefenseRecord = {
				model = model,
				piece = piece,
				routeId = if piece.cellX <= BuildGridConfig.width * 0.5 then "Left" else "Right",
				occupiedCells = occupiedCells,
				health = maximum,
				nextShotAt = 0,
			}
			self._records[id] = record
			self._byModel[model] = record
			if piece.pieceType == "Wall" then
				for _, cell in occupiedCells do
					self._wallIdByCell[GridMath.CellKey(cell.x, cell.z)] = id
				end
			end
		end
	end
end

function GridDefenseService.getLivePlan(self: Service): BuildPlan
	local pieces: { [string]: BuildPieceData } = {}
	for id, record in self._records do
		if record.model.Parent and record.health > 0 then
			pieces[id] = table.clone(record.piece)
		end
	end
	return {
		schemaVersion = self._schemaVersion,
		revision = self._revision,
		pieces = pieces,
	}
end

function GridDefenseService.getRouteDefenseState(self: Service, routeId: RouteId): RouteDefenseState
	local result: RouteDefenseState = {
		wallCount = 0,
		wallHealth = 0,
		slowTrapCount = 0,
	}
	for _, record in self._records do
		if record.routeId == routeId and record.model.Parent and record.health > 0 then
			if record.piece.pieceType == "Wall" then
				result.wallCount += 1
				result.wallHealth += record.health
			elseif record.piece.pieceType == "SlowTrap" then
				result.slowTrapCount += 1
			end
		end
	end
	return result
end

function GridDefenseService.findBlockingWall(
	self: Service,
	pathCellKeys: { string },
	pointIndex: number,
	position: Vector3,
	range: number
): Model?
	local attackRange = math.max(0, range)
	local maxLookaheadCells = math.ceil(attackRange / BuildGridConfig.cellSize) + 1
	local wallId = CombatRoutingPolicy.FirstBlockingWallId(
		pathCellKeys,
		pointIndex,
		self._wallIdByCell,
		maxLookaheadCells
	)
	local record = if wallId then self._records[wallId] else nil
	if
		not record
		or record.piece.pieceType ~= "Wall"
		or record.health <= 0
		or not record.model.Parent
		or not record.model.PrimaryPart
	then
		return nil
	end
	return if (record.model.PrimaryPart.Position - position).Magnitude <= attackRange
		then record.model
		else nil
end

function GridDefenseService.damageWall(
	self: Service,
	wall: Model,
	damage: number,
	enemyType: EnemyType,
	attackerRouteId: RouteId
): boolean
	local record = self._byModel[wall]
	if not record or record.piece.pieceType ~= "Wall" or record.health <= 0 then
		return false
	end
	local actualDamage = math.min(record.health, math.max(0, damage))
	record.health -= actualDamage
	wall:SetAttribute("Health", record.health)
	self._statsService:recordWallDamage(actualDamage)
	if record.health > 0 then
		return false
	end
	self._statsService:recordWallDestroyed(record.piece.id, enemyType)
	self._statsService:recordFirstBreach(attackerRouteId, record.piece.id, enemyType)
	for _, cell in record.occupiedCells do
		local key = GridMath.CellKey(cell.x, cell.z)
		if self._wallIdByCell[key] == record.piece.id then
			self._wallIdByCell[key] = nil
		end
	end
	self._records[record.piece.id] = nil
	self._byModel[wall] = nil
	wall:Destroy()
	return true
end

function GridDefenseService._update(self: Service, deltaTime: number)
	if self._stateService:getPhase() ~= "DEFENDING" or not self._enemyService then
		return
	end
	local enemyService = self._enemyService
	local now = os.clock()
	self._trapElapsed += deltaTime
	local updateTraps = self._trapElapsed >= 0.15
	if updateTraps then
		self._trapElapsed = 0
	end
	for _, record in self._records do
		local root = record.model.PrimaryPart
		if not root then
			continue
		end
		if record.piece.pieceType == "Turret" and now >= record.nextShotAt then
			local enemy = enemyService:findPriorityEnemy(root.Position, DefenseConfig.turret.range)
			if enemy and enemy.PrimaryPart then
				record.nextShotAt = now + DefenseConfig.turret.cooldownSeconds
				showTracer(
					self._runtimeDefenses,
					root.Position + Vector3.new(0, 3.8, 0),
					enemy.PrimaryPart.Position
				)
				self._statsService:recordTurretDamage(
					enemyService:damageEnemy(enemy, DefenseConfig.turret.damage)
				)
			end
		elseif record.piece.pieceType == "SlowTrap" and updateTraps then
			self._statsService:recordEnemiesSlowed(
				enemyService:applySlowInRadius(
					root.Position,
					DefenseConfig.slowTrap.effectRadius,
					DefenseConfig.slowTrap.slowMultiplier,
					DefenseConfig.slowTrap.effectDurationSeconds
				)
			)
		end
	end
end

return GridDefenseService
