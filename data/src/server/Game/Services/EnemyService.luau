--!strict

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

type GameState = "PREPARATION" | "STARTING" | "DEFENDING" | "VICTORY" | "DEFEAT" | "REVIEW"
type StateService = {
	getPhase: (self: StateService) -> GameState,
}
type EnemyConfigType = {
	maxHealth: number,
	moveSpeed: number,
	wallDetectionRange: number,
	wallAttackDamage: number,
	wallAttackCooldownSeconds: number,
	maxActiveEnemies: number,
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
local EnemyConfig = loadModule(configFolder:WaitForChild("EnemyConfig")) :: EnemyConfigType

type EnemyRecord = {
	model: Model,
	root: BasePart,
	health: number,
	nodeIndex: number,
	attackElapsed: number,
}

type FindNearestWall = (position: Vector3, range: number) -> Model?
type DamageWall = (wall: Model, damage: number) -> boolean
type ReachedCore = () -> ()

local EnemyService = {}
EnemyService.__index = EnemyService

export type Service = typeof(setmetatable(
	{} :: {
		_stateService: StateService,
		_template: Model,
		_spawnPart: BasePart,
		_core: BasePart,
		_nodes: { BasePart },
		_runtimeEnemies: Folder,
		_active: { [Model]: EnemyRecord },
		_spawnSerial: number,
		_findNearestWall: FindNearestWall?,
		_damageWall: DamageWall?,
		_reachedCore: ReachedCore?,
		_heartbeatConnection: RBXScriptConnection?,
	},
	EnemyService
))

local function findOrCreateFolder(parent: Instance, name: string): Folder
	local existing = parent:FindFirstChild(name)
	if existing then
		assert(existing:IsA("Folder"), string.format("%s must be a Folder", existing:GetFullName()))
		return existing
	end

	local folder = Instance.new("Folder")
	folder.Name = name
	folder.Parent = parent
	return folder
end

local function getHealthColor(ratio: number): Color3
	if ratio <= 0.3 then
		return Color3.fromRGB(230, 65, 65)
	end
	if ratio <= 0.6 then
		return Color3.fromRGB(255, 196, 61)
	end
	return Color3.fromRGB(73, 190, 103)
end

local function updateHealthBar(model: Model, health: number, maxHealth: number)
	local billboard = model:FindFirstChild("HealthBillboard", true)
	if not billboard or not billboard:IsA("BillboardGui") then
		return
	end

	local fill = billboard:FindFirstChild("Fill", true)
	if not fill or not fill:IsA("Frame") then
		return
	end

	local ratio = if maxHealth > 0 then math.clamp(health / maxHealth, 0, 1) else 0
	fill.Size = UDim2.fromScale(ratio, 1)
	fill.BackgroundColor3 = getHealthColor(ratio)
end

function EnemyService.new(prototype: Folder, templates: Folder, stateService: StateService): Service
	local enemySpawn = prototype:FindFirstChild("EnemySpawn")
	assert(enemySpawn and enemySpawn:IsA("BasePart"), "Prototype.EnemySpawn is required")

	local objectiveCore = prototype:FindFirstChild("ObjectiveCore")
	assert(objectiveCore and objectiveCore:IsA("BasePart"), "Prototype.ObjectiveCore is required")

	local lane = prototype:FindFirstChild("Lane")
	assert(lane and lane:IsA("Folder"), "Prototype.Lane is required")

	local nodes: { BasePart } = {}
	for _, child in lane:GetChildren() do
		if child:IsA("BasePart") then
			table.insert(nodes, child)
		end
	end
	table.sort(nodes, function(left: BasePart, right: BasePart): boolean
		return left.Name < right.Name
	end)
	assert(#nodes == 4, "Challenge 1 requires exactly four lane nodes")

	local template = templates:FindFirstChild("BasicZombie")
	assert(template and template:IsA("Model"), "GameTemplates.BasicZombie is required")
	assert(template.PrimaryPart, "BasicZombie.PrimaryPart is required")

	local runtime = findOrCreateFolder(prototype, "Runtime")
	local runtimeEnemies = findOrCreateFolder(runtime, "Enemies")

	local self: Service = setmetatable({
		_stateService = stateService,
		_template = template,
		_spawnPart = enemySpawn,
		_core = objectiveCore,
		_nodes = nodes,
		_runtimeEnemies = runtimeEnemies,
		_active = {},
		_spawnSerial = 0,
		_findNearestWall = nil,
		_damageWall = nil,
		_reachedCore = nil,
		_heartbeatConnection = nil,
	}, EnemyService)

	self._heartbeatConnection = RunService.Heartbeat:Connect(function(deltaTime: number)
		self:_update(math.min(deltaTime, 0.1))
	end)

	return self
end

function EnemyService.setCombatCallbacks(
	self: Service,
	findNearestWall: FindNearestWall,
	damageWall: DamageWall,
	reachedCore: ReachedCore
)
	self._findNearestWall = findNearestWall
	self._damageWall = damageWall
	self._reachedCore = reachedCore
end

function EnemyService.spawn(self: Service): boolean
	if self._stateService:getPhase() ~= "DEFENDING" then
		return false
	end
	if self:getActiveCount() >= EnemyConfig.maxActiveEnemies then
		return false
	end

	local model = self._template:Clone()
	local root = model.PrimaryPart
	assert(root, "Cloned BasicZombie.PrimaryPart is required")

	self._spawnSerial += 1
	model.Name = string.format("BasicZombie_%03d", self._spawnSerial)
	model:SetAttribute("MaxHealth", EnemyConfig.maxHealth)
	model:SetAttribute("Health", EnemyConfig.maxHealth)
	model:PivotTo(CFrame.new(self._spawnPart.Position + Vector3.new(0, 2, 0)))
	model.Parent = self._runtimeEnemies
	updateHealthBar(model, EnemyConfig.maxHealth, EnemyConfig.maxHealth)

	self._active[model] = {
		model = model,
		root = root,
		health = EnemyConfig.maxHealth,
		nodeIndex = 1,
		attackElapsed = 0,
	}
	return true
end

function EnemyService.getActiveCount(self: Service): number
	local count = 0
	for _ in self._active do
		count += 1
	end
	return count
end

function EnemyService.findNearestEnemy(self: Service, position: Vector3, range: number): Model?
	local nearest: Model? = nil
	local nearestDistance = range

	for model, record in self._active do
		if model.Parent and record.health > 0 then
			local distance = (record.root.Position - position).Magnitude
			if distance <= nearestDistance then
				nearest = model
				nearestDistance = distance
			end
		end
	end

	return nearest
end

function EnemyService.damageEnemy(self: Service, enemy: Model, damage: number): boolean
	local record = self._active[enemy]
	if not record or record.health <= 0 then
		return false
	end

	record.health = math.max(0, record.health - math.max(0, damage))
	enemy:SetAttribute("Health", record.health)
	updateHealthBar(enemy, record.health, EnemyConfig.maxHealth)
	if record.health > 0 then
		return false
	end

	self:_remove(record)
	return true
end

function EnemyService.clear(self: Service)
	for _, record in self._active do
		record.model:Destroy()
	end
	table.clear(self._active)
end

function EnemyService._remove(self: Service, record: EnemyRecord)
	self._active[record.model] = nil
	record.model:Destroy()
end

function EnemyService._update(self: Service, deltaTime: number)
	if self._stateService:getPhase() ~= "DEFENDING" then
		return
	end

	for model, record in self._active do
		if not model.Parent then
			self._active[model] = nil
			continue
		end

		local wall = if self._findNearestWall
			then self._findNearestWall(record.root.Position, EnemyConfig.wallDetectionRange)
			else nil
		if wall and self._damageWall then
			record.attackElapsed += deltaTime
			if record.attackElapsed >= EnemyConfig.wallAttackCooldownSeconds then
				record.attackElapsed -= EnemyConfig.wallAttackCooldownSeconds
				self._damageWall(wall, EnemyConfig.wallAttackDamage)
			end
			continue
		end

		record.attackElapsed = 0
		local targetPosition: Vector3
		if record.nodeIndex <= #self._nodes then
			targetPosition = self._nodes[record.nodeIndex].Position + Vector3.new(0, 2, 0)
		else
			targetPosition = Vector3.new(self._core.Position.X, 2, self._core.Position.Z)
		end

		local offset = targetPosition - record.root.Position
		local distance = offset.Magnitude
		if distance <= 0.25 then
			if record.nodeIndex <= #self._nodes then
				record.nodeIndex += 1
			else
				self:_remove(record)
				if self._reachedCore then
					self._reachedCore()
				end
			end
			continue
		end

		local movement = math.min(distance, EnemyConfig.moveSpeed * deltaTime)
		local nextPosition = record.root.Position + offset.Unit * movement
		local lookPosition = Vector3.new(targetPosition.X, nextPosition.Y, targetPosition.Z)
		record.model:PivotTo(CFrame.lookAt(nextPosition, lookPosition))
	end
end

return EnemyService
