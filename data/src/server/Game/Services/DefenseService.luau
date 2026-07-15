--!strict

local Debris = game:GetService("Debris")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

type GameState = "PREPARATION" | "STARTING" | "DEFENDING" | "VICTORY" | "DEFEAT" | "REVIEW"
type DefenseType = "Empty" | "Wall" | "SlowTrap" | "Turret"
type EnemyType = "Roamer" | "Brute"
type RouteId = "Left" | "Right"
type StateService = {
	getPhase: (self: StateService) -> GameState,
}
type EnemyService = {
	findPriorityEnemy: (self: EnemyService, position: Vector3, range: number) -> Model?,
	damageEnemy: (self: EnemyService, enemy: Model, damage: number) -> number,
	applySlowInRadius: (
		self: EnemyService,
		position: Vector3,
		radius: number,
		multiplier: number,
		durationSeconds: number,
		padId: string
	) -> number,
}
type StatsService = {
	recordWallDamage: (self: StatsService, amount: number) -> (),
	recordTurretDamage: (self: StatsService, amount: number) -> (),
	recordEnemiesSlowed: (self: StatsService, count: number) -> (),
	recordFirstBreach: (
		self: StatsService,
		routeId: RouteId,
		padId: string,
		enemyType: EnemyType
	) -> boolean,
	recordWallDestroyed: (self: StatsService, padId: string, enemyType: EnemyType) -> (),
}
type DefenseConfigType = {
	wall: { maxHealth: number },
	slowTrap: {
		maxHealth: number,
		slowMultiplier: number,
		effectDurationSeconds: number,
		effectRadius: number,
	},
	turret: {
		maxHealth: number,
		range: number,
		damage: number,
		cooldownSeconds: number,
	},
}
type RouteDefenseState = {
	wallCount: number,
	wallHealth: number,
	slowTrapCount: number,
}
type DefenseRecord = {
	model: Model,
	pad: BasePart,
	defenseType: DefenseType,
	routeId: RouteId,
	health: number,
	maxHealth: number,
	nextShotAt: number,
}

local runtimeRequire = require
local configFolder =
	ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Game"):WaitForChild("Config")
local DefenseConfig =
	runtimeRequire(configFolder:WaitForChild("DefenseConfig") :: ModuleScript) :: DefenseConfigType

local DefenseService = {}
DefenseService.__index = DefenseService

export type Service = typeof(setmetatable(
	{} :: {
		_stateService: StateService,
		_statsService: StatsService,
		_templates: Folder,
		_runtimeDefenses: Folder,
		_byPad: { [string]: DefenseRecord },
		_byModel: { [Model]: DefenseRecord },
		_enemyService: EnemyService?,
		_trapElapsed: number,
		_heartbeatConnection: RBXScriptConnection,
	},
	DefenseService
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

local function maxHealthFor(defenseType: DefenseType): number
	if defenseType == "Wall" then
		return DefenseConfig.wall.maxHealth
	elseif defenseType == "SlowTrap" then
		return DefenseConfig.slowTrap.maxHealth
	elseif defenseType == "Turret" then
		return DefenseConfig.turret.maxHealth
	end
	return 0
end

local function offsetFor(defenseType: DefenseType): number
	if defenseType == "Wall" then
		return 3.05
	elseif defenseType == "SlowTrap" then
		return 0.55
	end
	return 0.9
end

local function updateLabel(record: DefenseRecord)
	local label = record.model:FindFirstChild("Label", true)
	if not label or not label:IsA("TextLabel") then
		return
	end
	if record.defenseType == "Wall" then
		label.Text = string.format("MUR • %d PV", math.ceil(record.health))
	end
end

local function showTracer(parent: Instance, origin: Vector3, target: Vector3)
	local offset = target - origin
	local distance = offset.Magnitude
	if distance <= 0.1 then
		return
	end
	local tracer = Instance.new("Part")
	tracer.Name = "TurretTracer"
	tracer.Anchored = true
	tracer.CanCollide = false
	tracer.CanQuery = false
	tracer.CanTouch = false
	tracer.CastShadow = false
	tracer.Material = Enum.Material.Neon
	tracer.Color = Color3.fromRGB(90, 220, 255)
	tracer.Size = Vector3.new(0.14, 0.14, distance)
	tracer.CFrame = CFrame.lookAt(origin, target) * CFrame.new(0, 0, -distance * 0.5)
	tracer.Parent = parent
	Debris:AddItem(tracer, 0.08)
end

function DefenseService.new(
	prototype: Folder,
	templates: Folder,
	stateService: StateService,
	statsService: StatsService
): Service
	for _, name in ipairs({ "Wall", "SlowTrap", "Turret" }) do
		local template = templates:FindFirstChild(name)
		assert(
			template and template:IsA("Model") and template.PrimaryPart,
			name .. " template is invalid"
		)
	end
	local runtime = findOrCreateFolder(prototype, "Runtime")
	local runtimeDefenses = findOrCreateFolder(runtime, "Defenses")
	local placeholder = RunService.Heartbeat:Connect(function() end)
	local self: Service = setmetatable({
		_stateService = stateService,
		_statsService = statsService,
		_templates = templates,
		_runtimeDefenses = runtimeDefenses,
		_byPad = {},
		_byModel = {},
		_enemyService = nil,
		_trapElapsed = 0,
		_heartbeatConnection = placeholder,
	}, DefenseService)
	placeholder:Disconnect()
	self._heartbeatConnection = RunService.Heartbeat:Connect(function(deltaTime: number)
		self:_update(math.min(deltaTime, 0.1))
	end)
	return self
end

function DefenseService.setEnemyService(self: Service, enemyService: EnemyService)
	self._enemyService = enemyService
end

function DefenseService.place(self: Service, pad: BasePart, defenseType: DefenseType)
	local existing = self._byPad[pad.Name]
	if existing then
		self._byPad[pad.Name] = nil
		self._byModel[existing.model] = nil
		existing.model:Destroy()
	end
	if defenseType == "Empty" then
		return
	end

	local template = self._templates:FindFirstChild(defenseType)
	assert(
		template and template:IsA("Model") and template.PrimaryPart,
		"Missing template " .. defenseType
	)
	local routeValue = pad:GetAttribute("RouteId")
	assert(routeValue == "Left" or routeValue == "Right", pad.Name .. " has invalid RouteId")
	local routeId: RouteId = if routeValue == "Left" then "Left" else "Right"
	local maximum = maxHealthFor(defenseType)
	local model = template:Clone()
	model.Name = string.format("%s_%s", pad.Name, defenseType)
	model:SetAttribute("DefenseType", defenseType)
	model:SetAttribute("PadId", pad.Name)
	model:SetAttribute("RouteId", routeId)
	model:SetAttribute("MaxHealth", maximum)
	model:SetAttribute("Health", maximum)
	model:PivotTo(pad.CFrame * CFrame.new(0, offsetFor(defenseType), 0))
	model.Parent = self._runtimeDefenses
	local record: DefenseRecord = {
		model = model,
		pad = pad,
		defenseType = defenseType,
		routeId = routeId,
		health = maximum,
		maxHealth = maximum,
		nextShotAt = 0,
	}
	self._byPad[pad.Name] = record
	self._byModel[model] = record
	updateLabel(record)
end

function DefenseService.getRouteDefenseState(self: Service, routeId: RouteId): RouteDefenseState
	local result: RouteDefenseState = { wallCount = 0, wallHealth = 0, slowTrapCount = 0 }
	for _, record in self._byPad do
		if record.routeId == routeId and record.model.Parent then
			if record.defenseType == "Wall" and record.health > 0 then
				result.wallCount += 1
				result.wallHealth += record.health
			elseif record.defenseType == "SlowTrap" then
				result.slowTrapCount += 1
			end
		end
	end
	return result
end

function DefenseService.findBlockingWall(
	self: Service,
	routeId: RouteId,
	position: Vector3,
	range: number
): Model?
	local selected: Model? = nil
	local selectedDistance = math.max(0, range)
	for _, record in self._byPad do
		if record.routeId == routeId and record.defenseType == "Wall" and record.health > 0 then
			local root = record.model.PrimaryPart
			if root then
				local distance = (root.Position - position).Magnitude
				if distance <= selectedDistance then
					selected = record.model
					selectedDistance = distance
				end
			end
		end
	end
	return selected
end

function DefenseService.damageWall(
	self: Service,
	wall: Model,
	damage: number,
	enemyType: EnemyType
): boolean
	local record = self._byModel[wall]
	if not record or record.defenseType ~= "Wall" or record.health <= 0 then
		return false
	end
	local actualDamage = math.min(record.health, math.max(0, damage))
	record.health -= actualDamage
	wall:SetAttribute("Health", record.health)
	self._statsService:recordWallDamage(actualDamage)
	updateLabel(record)
	if record.health > 0 then
		return false
	end

	self._statsService:recordWallDestroyed(record.pad.Name, enemyType)
	self._statsService:recordFirstBreach(record.routeId, record.pad.Name, enemyType)
	self._byPad[record.pad.Name] = nil
	self._byModel[wall] = nil
	wall:Destroy()
	return true
end

function DefenseService._update(self: Service, deltaTime: number)
	if self._stateService:getPhase() ~= "DEFENDING" then
		return
	end
	local enemyService = self._enemyService
	if not enemyService then
		return
	end
	local now = os.clock()
	self._trapElapsed += deltaTime
	local updateTraps = self._trapElapsed >= 0.15
	if updateTraps then
		self._trapElapsed = 0
	end

	for _, record in self._byPad do
		local root = record.model.PrimaryPart
		if not root then
			continue
		end
		if record.defenseType == "Turret" and now >= record.nextShotAt then
			local enemy = enemyService:findPriorityEnemy(root.Position, DefenseConfig.turret.range)
			if enemy and enemy.PrimaryPart then
				record.nextShotAt = now + DefenseConfig.turret.cooldownSeconds
				showTracer(
					self._runtimeDefenses,
					root.Position + Vector3.new(0, 3.8, 0),
					enemy.PrimaryPart.Position
				)
				local damage = enemyService:damageEnemy(enemy, DefenseConfig.turret.damage)
				self._statsService:recordTurretDamage(damage)
			end
		elseif record.defenseType == "SlowTrap" and updateTraps then
			local count = enemyService:applySlowInRadius(
				root.Position,
				DefenseConfig.slowTrap.effectRadius,
				DefenseConfig.slowTrap.slowMultiplier,
				DefenseConfig.slowTrap.effectDurationSeconds,
				record.pad.Name
			)
			self._statsService:recordEnemiesSlowed(count)
		end
	end
end

return DefenseService
