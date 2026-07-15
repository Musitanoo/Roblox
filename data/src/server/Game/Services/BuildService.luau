--!strict

local Debris = game:GetService("Debris")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

type GameState = "PREPARATION" | "STARTING" | "DEFENDING" | "VICTORY" | "DEFEAT" | "REVIEW"
type DefenseType = "Empty" | "Wall" | "Turret"
type DefenseSnapshot = { [string]: DefenseType }
type StateService = {
	getPhase: (self: StateService) -> GameState,
}
type DefenseConfigType = {
	interactionDistance: number,
	requestCooldownSeconds: number,
	wall: {
		maxHealth: number,
	},
	turret: {
		range: number,
		damage: number,
		cooldownSeconds: number,
	},
}
type GameTypesModule = {
	isDefenseType: (value: unknown) -> boolean,
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
local DefenseConfig = loadModule(configFolder:WaitForChild("DefenseConfig")) :: DefenseConfigType
local GameTypes = loadModule(sharedGame:WaitForChild("GameTypes")) :: GameTypesModule

type FindNearestEnemy = (position: Vector3, range: number) -> Model?
type DamageEnemy = (enemy: Model, damage: number) -> ()
type DestroyedCallback = (description: string) -> ()

local BuildService = {}
BuildService.__index = BuildService

export type Service = typeof(setmetatable(
	{} :: {
		_stateService: StateService,
		_templates: Folder,
		_buildPads: Folder,
		_runtimeDefenses: Folder,
		_pads: { [string]: BasePart },
		_currentByPad: { [string]: Model },
		_requestTimes: { [Player]: number },
		_findNearestEnemy: FindNearestEnemy?,
		_damageEnemy: DamageEnemy?,
		_destroyedCallback: DestroyedCallback?,
		_heartbeatConnection: RBXScriptConnection?,
	},
	BuildService
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
	tracer.Color = Color3.fromRGB(82, 210, 255)
	tracer.Size = Vector3.new(0.16, 0.16, distance)
	tracer.CFrame = CFrame.lookAt(origin, target) * CFrame.new(0, 0, -distance / 2)
	tracer.Parent = parent
	Debris:AddItem(tracer, 0.09)
end

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

function BuildService.new(
	prototype: Folder,
	templates: Folder,
	requestBuild: RemoteEvent,
	stateService: StateService
): Service
	local buildPads = prototype:FindFirstChild("BuildPads")
	assert(buildPads and buildPads:IsA("Folder"), "Prototype.BuildPads is required")

	local runtime = findOrCreateFolder(prototype, "Runtime")
	local runtimeDefenses = findOrCreateFolder(runtime, "Defenses")

	local pads: { [string]: BasePart } = {}
	for _, child in buildPads:GetChildren() do
		if child:IsA("BasePart") then
			pads[child.Name] = child
		end
	end

	local self: Service = setmetatable({
		_stateService = stateService,
		_templates = templates,
		_buildPads = buildPads,
		_runtimeDefenses = runtimeDefenses,
		_pads = pads,
		_currentByPad = {},
		_requestTimes = {},
		_findNearestEnemy = nil,
		_damageEnemy = nil,
		_destroyedCallback = nil,
		_heartbeatConnection = nil,
	}, BuildService)

	requestBuild.OnServerEvent:Connect(
		function(player: Player, padName: unknown, defenseType: unknown)
			self:_handleRequest(player, padName, defenseType)
		end
	)

	Players.PlayerRemoving:Connect(function(player: Player)
		self._requestTimes[player] = nil
	end)

	self._heartbeatConnection = RunService.Heartbeat:Connect(function()
		self:_updateTurrets()
	end)

	return self
end

function BuildService.setEnemyCallbacks(
	self: Service,
	findNearestEnemy: FindNearestEnemy,
	damageEnemy: DamageEnemy
)
	self._findNearestEnemy = findNearestEnemy
	self._damageEnemy = damageEnemy
end

function BuildService.setDestroyedCallback(self: Service, callback: DestroyedCallback)
	self._destroyedCallback = callback
end

function BuildService.setBuildEnabled(self: Service, enabled: boolean)
	for _, pad in self._pads do
		local prompt = pad:FindFirstChild("BuildPrompt")
		if prompt and prompt:IsA("ProximityPrompt") then
			prompt.Enabled = enabled
		end
	end
end

function BuildService._handleRequest(
	self: Service,
	player: Player,
	padNameValue: unknown,
	defenseTypeValue: unknown
)
	if player.Parent ~= Players then
		return
	end
	if typeof(padNameValue) ~= "string" or #padNameValue > 16 then
		return
	end
	if not GameTypes.isDefenseType(defenseTypeValue) then
		return
	end

	local now = os.clock()
	local previousRequest = self._requestTimes[player]
	if previousRequest and now - previousRequest < DefenseConfig.requestCooldownSeconds then
		return
	end
	self._requestTimes[player] = now

	if self._stateService:getPhase() ~= "PREPARATION" then
		return
	end

	local pad = self._pads[padNameValue]
	if not pad or pad.Parent ~= self._buildPads then
		return
	end

	local playerRoot = getPlayerRoot(player)
	if not playerRoot then
		return
	end
	if (playerRoot.Position - pad.Position).Magnitude > DefenseConfig.interactionDistance then
		return
	end

	self:_place(padNameValue, defenseTypeValue :: DefenseType)
end

function BuildService._place(self: Service, padName: string, defenseType: DefenseType)
	local pad = self._pads[padName]
	if not pad then
		return
	end

	local current = self._currentByPad[padName]
	if current then
		current:Destroy()
		self._currentByPad[padName] = nil
	end

	pad:SetAttribute("DefenseType", defenseType)
	if defenseType == "Empty" then
		return
	end

	local template = self._templates:FindFirstChild(defenseType)
	assert(template and template:IsA("Model"), string.format("Missing %s template", defenseType))

	local model = template:Clone()
	model.Name = string.format("%s_%s", padName, defenseType)
	model:SetAttribute("DefenseType", defenseType)
	model:SetAttribute("PadName", padName)

	if defenseType == "Wall" then
		model:SetAttribute("MaxHealth", DefenseConfig.wall.maxHealth)
		model:SetAttribute("Health", DefenseConfig.wall.maxHealth)
		model:PivotTo(pad.CFrame * CFrame.new(0, 3.2, 0))
	else
		model:SetAttribute("NextShotAt", 0)
		model:PivotTo(pad.CFrame * CFrame.new(0, 0.7, 0))
	end

	model.Parent = self._runtimeDefenses
	self._currentByPad[padName] = model
	if defenseType == "Wall" then
		updateHealthBar(model, DefenseConfig.wall.maxHealth, DefenseConfig.wall.maxHealth)
	end
end

function BuildService.snapshot(self: Service): DefenseSnapshot
	local snapshot: DefenseSnapshot = {}
	for padName, pad in self._pads do
		local defenseType = pad:GetAttribute("DefenseType")
		if GameTypes.isDefenseType(defenseType) then
			snapshot[padName] = defenseType :: DefenseType
		else
			snapshot[padName] = "Empty"
		end
	end
	return snapshot
end

function BuildService.restore(self: Service, snapshot: DefenseSnapshot)
	for padName in self._pads do
		local defenseType: DefenseType = snapshot[padName]
		if not defenseType then
			defenseType = "Empty"
		end
		self:_place(padName, defenseType)
	end
end

function BuildService.findNearestWall(self: Service, position: Vector3, range: number): Model?
	local nearest: Model? = nil
	local nearestDistance = range

	for _, model in self._currentByPad do
		if model.Parent and model:GetAttribute("DefenseType") == "Wall" then
			local primaryPart = model.PrimaryPart
			local health = model:GetAttribute("Health")
			if primaryPart and typeof(health) == "number" and health > 0 then
				local distance = (primaryPart.Position - position).Magnitude
				if distance <= nearestDistance then
					nearest = model
					nearestDistance = distance
				end
			end
		end
	end

	return nearest
end

function BuildService.damageWall(self: Service, wall: Model, damage: number): boolean
	local padName = wall:GetAttribute("PadName")
	if typeof(padName) ~= "string" or self._currentByPad[padName] ~= wall then
		return false
	end

	local currentHealth = wall:GetAttribute("Health")
	if typeof(currentHealth) ~= "number" or currentHealth <= 0 then
		return false
	end

	local nextHealth = math.max(0, currentHealth - math.max(0, damage))
	wall:SetAttribute("Health", nextHealth)
	updateHealthBar(wall, nextHealth, DefenseConfig.wall.maxHealth)
	if nextHealth > 0 then
		return false
	end

	self._currentByPad[padName] = nil
	wall:Destroy()
	if self._destroyedCallback then
		self._destroyedCallback(string.format("%s (Mur)", padName))
	end
	return true
end

function BuildService._updateTurrets(self: Service)
	if self._stateService:getPhase() ~= "DEFENDING" then
		return
	end
	if not self._findNearestEnemy or not self._damageEnemy then
		return
	end

	local now = os.clock()
	for _, model in self._currentByPad do
		if model.Parent and model:GetAttribute("DefenseType") == "Turret" then
			local primaryPart = model.PrimaryPart
			local nextShotAt = model:GetAttribute("NextShotAt")
			if primaryPart and (typeof(nextShotAt) ~= "number" or now >= nextShotAt) then
				local enemy =
					self._findNearestEnemy(primaryPart.Position, DefenseConfig.turret.range)
				if enemy then
					model:SetAttribute("NextShotAt", now + DefenseConfig.turret.cooldownSeconds)
					local targetPart = enemy.PrimaryPart
					local muzzle = model:FindFirstChild("Muzzle", true)
					local originPart: BasePart = primaryPart
					if muzzle and muzzle:IsA("BasePart") then
						originPart = muzzle
					end
					if targetPart then
						showTracer(self._runtimeDefenses, originPart.Position, targetPart.Position)
					end
					self._damageEnemy(enemy, DefenseConfig.turret.damage)
				end
			end
		end
	end
end

return BuildService
