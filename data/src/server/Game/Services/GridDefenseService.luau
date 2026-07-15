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
type StateService = { getPhase: (self: StateService) -> GameState }
type EnemyService = {
	findPriorityEnemy: (self: EnemyService, position: Vector3, range: number) -> Model?,
	damageEnemy: (self: EnemyService, enemy: Model, damage: number) -> number,
	applySlowInRadius: (self: EnemyService, Vector3, number, number, number, string) -> number,
}
type StatsService = {
	recordWallDamage: (self: StatsService, number) -> (),
	recordTurretDamage: (self: StatsService, number) -> (),
	recordEnemiesSlowed: (self: StatsService, number) -> (),
	recordFirstBreach: (self: StatsService, RouteId, string, EnemyType) -> boolean,
	recordWallDestroyed: (self: StatsService, string, EnemyType) -> (),
}
type DefenseConfigType = {
	wall: { maxHealth: number },
	slowTrap: {
		maxHealth: number,
		slowMultiplier: number,
		effectDurationSeconds: number,
		effectRadius: number,
	},
	turret: { maxHealth: number, range: number, damage: number, cooldownSeconds: number },
}
type DefenseRecord = {
	model: Model,
	piece: BuildPieceData,
	routeId: RouteId,
	health: number,
	nextShotAt: number,
}

local config = ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Game"):WaitForChild("Config")
local DefenseConfig =
	require(config:WaitForChild("DefenseConfig") :: ModuleScript) :: DefenseConfigType

local GridDefenseService = {}
GridDefenseService.__index = GridDefenseService

export type Service = typeof(setmetatable(
	{} :: {
		_stateService: StateService,
		_statsService: StatsService,
		_runtimeDefenses: Folder,
		_records: { [string]: DefenseRecord },
		_byModel: { [Model]: DefenseRecord },
		_enemyService: EnemyService?,
		_trapElapsed: number,
		_heartbeatConnection: RBXScriptConnection,
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
	_stateTemplates: Folder,
	stateService: StateService,
	statsService: StatsService
): Service
	local runtime = findOrCreateFolder(prototype, "Runtime")
	local runtimeDefenses = findOrCreateFolder(runtime, "Defenses")
	local placeholder = RunService.Heartbeat:Connect(function() end)
	local self: Service = setmetatable({
		_stateService = stateService,
		_statsService = statsService,
		_runtimeDefenses = runtimeDefenses,
		_records = {},
		_byModel = {},
		_enemyService = nil,
		_trapElapsed = 0,
		_heartbeatConnection = placeholder,
	}, GridDefenseService)
	placeholder:Disconnect()
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
	for id, piece in plan.pieces do
		local model: Model? = nil
		for _, candidate in self._runtimeDefenses:GetChildren() do
			if candidate:IsA("Model") and candidate:GetAttribute("PieceId") == id then
				model = candidate
				break
			end
		end
		if model and model:IsA("Model") then
			local maximum = if piece.pieceType == "Wall"
				then DefenseConfig.wall.maxHealth
				elseif piece.pieceType == "SlowTrap" then DefenseConfig.slowTrap.maxHealth
				else DefenseConfig.turret.maxHealth
			model:SetAttribute("Health", maximum)
			model:SetAttribute("MaxHealth", maximum)
			local record: DefenseRecord = {
				model = model,
				piece = piece,
				routeId = if piece.cellX <= 8 then "Left" else "Right",
				health = maximum,
				nextShotAt = 0,
			}
			self._records[id] = record
			self._byModel[model] = record
		end
	end
end

function GridDefenseService.findBlockingWall(
	self: Service,
	_routeId: RouteId,
	position: Vector3,
	range: number
): Model?
	local selected: Model? = nil
	local selectedDistance = math.max(0, range)
	for _, record in self._records do
		if record.piece.pieceType == "Wall" and record.health > 0 and record.model.PrimaryPart then
			local distance = (record.model.PrimaryPart.Position - position).Magnitude
			if distance <= selectedDistance then
				selected = record.model
				selectedDistance = distance
			end
		end
	end
	return selected
end

function GridDefenseService.damageWall(
	self: Service,
	wall: Model,
	damage: number,
	enemyType: EnemyType
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
	self._statsService:recordFirstBreach(record.routeId, record.piece.id, enemyType)
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
	for id, record in self._records do
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
					DefenseConfig.slowTrap.effectDurationSeconds,
					id
				)
			)
		end
	end
end

return GridDefenseService
