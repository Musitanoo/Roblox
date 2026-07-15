--!strict

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

type GameState = "PREPARATION" | "STARTING" | "DEFENDING" | "VICTORY" | "DEFEAT" | "REVIEW"
type DefenseType = "Empty" | "Wall" | "SlowTrap" | "Turret"
type DefenseSnapshot = { [string]: DefenseType }
type StateService = {
	getPhase: (self: StateService) -> GameState,
}
type DefenseConfigType = {
	maxBudget: number,
	interactionDistance: number,
	requestCooldownSeconds: number,
	costs: { [string]: number },
}
type GameTypesModule = {
	isDefenseType: (value: unknown) -> boolean,
}
type PlacementCallback = (pad: BasePart, defenseType: DefenseType) -> ()

local runtimeRequire = require
local sharedGame = ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Game")
local configFolder = sharedGame:WaitForChild("Config")
local DefenseConfig =
	runtimeRequire(configFolder:WaitForChild("DefenseConfig") :: ModuleScript) :: DefenseConfigType
local GameTypes =
	runtimeRequire(sharedGame:WaitForChild("GameTypes") :: ModuleScript) :: GameTypesModule

local BuildService = {}
BuildService.__index = BuildService

export type Service = typeof(setmetatable(
	{} :: {
		_replicaRoot: Folder,
		_stateService: StateService,
		_requestBuild: RemoteEvent,
		_buildPads: Folder,
		_pads: { [string]: BasePart },
		_currentTypes: { [string]: DefenseType },
		_usedBudget: number,
		_requestTimes: { [Player]: number },
		_processing: { [Player]: boolean },
		_placementCallback: PlacementCallback?,
	},
	BuildService
))

local function getPlayerRoot(player: Player): BasePart?
	local character = player.Character
	if not character then
		return nil
	end
	local root = character:FindFirstChild("HumanoidRootPart")
	return if root and root:IsA("BasePart") then root else nil
end

function BuildService.new(
	prototype: Folder,
	requestBuild: RemoteEvent,
	stateService: StateService,
	replicaRoot: Folder
): Service
	local buildPads = prototype:FindFirstChild("BuildPads")
	assert(buildPads and buildPads:IsA("Folder"), "Prototype.BuildPads is required")

	local pads: { [string]: BasePart } = {}
	local currentTypes: { [string]: DefenseType } = {}
	for _, child in buildPads:GetChildren() do
		if child:IsA("BasePart") then
			assert(
				typeof(child:GetAttribute("RouteId")) == "string",
				child.Name .. " requires RouteId"
			)
			pads[child.Name] = child
			currentTypes[child.Name] = "Empty"
			child:SetAttribute("DefenseType", "Empty")
		end
	end
	assert(#buildPads:GetChildren() == 8, "Defense Loop 0.2 requires exactly eight BuildPads")

	local self: Service = setmetatable({
		_replicaRoot = replicaRoot,
		_stateService = stateService,
		_requestBuild = requestBuild,
		_buildPads = buildPads,
		_pads = pads,
		_currentTypes = currentTypes,
		_usedBudget = 0,
		_requestTimes = {},
		_processing = {},
		_placementCallback = nil,
	}, BuildService)

	replicaRoot:SetAttribute("BudgetUsed", 0)
	replicaRoot:SetAttribute("BudgetMax", DefenseConfig.maxBudget)
	requestBuild.OnServerEvent:Connect(
		function(player: Player, padId: unknown, defenseType: unknown)
			self:_handleRequest(player, padId, defenseType)
		end
	)
	Players.PlayerRemoving:Connect(function(player: Player)
		self._requestTimes[player] = nil
		self._processing[player] = nil
	end)
	return self
end

function BuildService.setPlacementCallback(self: Service, callback: PlacementCallback)
	self._placementCallback = callback
end

function BuildService._reply(self: Service, player: Player, accepted: boolean, message: string)
	self._requestBuild:FireClient(player, accepted, string.sub(message, 1, 64))
end

function BuildService._handleRequest(
	self: Service,
	player: Player,
	padIdValue: unknown,
	defenseTypeValue: unknown
)
	if player.Parent ~= Players or self._processing[player] then
		return
	end
	self._processing[player] = true

	local function reject(message: string)
		self._processing[player] = nil
		self:_reply(player, false, message)
	end

	if typeof(padIdValue) ~= "string" or #padIdValue > 20 then
		reject("Emplacement invalide")
		return
	end
	if not GameTypes.isDefenseType(defenseTypeValue) then
		reject("Défense invalide")
		return
	end

	local now = os.clock()
	local previous = self._requestTimes[player]
	if previous and now - previous < DefenseConfig.requestCooldownSeconds then
		reject("Action trop rapide")
		return
	end
	self._requestTimes[player] = now

	if self._stateService:getPhase() ~= "PREPARATION" then
		reject("Construction verrouillée")
		return
	end

	local pad = self._pads[padIdValue]
	if not pad or pad.Parent ~= self._buildPads then
		reject("Emplacement invalide")
		return
	end
	local root = getPlayerRoot(player)
	if not root or (root.Position - pad.Position).Magnitude > DefenseConfig.interactionDistance then
		reject("Approchez-vous du pad")
		return
	end

	local defenseType: DefenseType
	if defenseTypeValue == "Wall" then
		defenseType = "Wall"
	elseif defenseTypeValue == "SlowTrap" then
		defenseType = "SlowTrap"
	elseif defenseTypeValue == "Turret" then
		defenseType = "Turret"
	else
		defenseType = "Empty"
	end
	local previousType = self._currentTypes[padIdValue]
	local nextBudget = self._usedBudget
		- (DefenseConfig.costs[previousType] or 0)
		+ (DefenseConfig.costs[defenseType] or DefenseConfig.maxBudget + 1)
	if nextBudget > DefenseConfig.maxBudget then
		reject("Budget insuffisant")
		return
	end

	self:_apply(padIdValue, defenseType)
	self._processing[player] = nil
	self:_reply(player, true, "Construction mise à jour")
end

function BuildService._updatePadLabel(_self: Service, pad: BasePart, defenseType: DefenseType)
	local label = pad:FindFirstChild("Label", true)
	if label and label:IsA("TextLabel") then
		local display = if defenseType == "Empty"
			then "VIDE"
			elseif defenseType == "SlowTrap" then "PIÈGE"
			elseif defenseType == "Wall" then "MUR"
			else "TOURELLE"
		label.Text = string.format("%s\n%s", pad.Name, display)
	end
end

function BuildService._recalculateBudget(self: Service)
	local used = 0
	for _, defenseType in self._currentTypes do
		used += DefenseConfig.costs[defenseType] or 0
	end
	self._usedBudget = used
	self._replicaRoot:SetAttribute("BudgetUsed", used)
end

function BuildService._apply(self: Service, padId: string, defenseType: DefenseType)
	local pad = self._pads[padId]
	assert(pad, "Unknown BuildPad " .. padId)
	self._currentTypes[padId] = defenseType
	pad:SetAttribute("DefenseType", defenseType)
	self:_updatePadLabel(pad, defenseType)
	if self._placementCallback then
		self._placementCallback(pad, defenseType)
	end
	self:_recalculateBudget()
end

function BuildService.snapshot(self: Service): DefenseSnapshot
	local snapshot = table.clone(self._currentTypes) :: DefenseSnapshot
	return snapshot
end

function BuildService.restore(self: Service, snapshot: DefenseSnapshot)
	for padId in self._pads do
		local snapshotType = snapshot[padId]
		local defenseType: DefenseType
		if snapshotType == "Wall" then
			defenseType = "Wall"
		elseif snapshotType == "SlowTrap" then
			defenseType = "SlowTrap"
		elseif snapshotType == "Turret" then
			defenseType = "Turret"
		else
			defenseType = "Empty"
		end
		self:_apply(padId, defenseType)
	end
	self:_recalculateBudget()
end

function BuildService.setBuildEnabled(self: Service, enabled: boolean)
	for _, pad in self._pads do
		local prompt = pad:FindFirstChild("BuildPrompt")
		if prompt and prompt:IsA("ProximityPrompt") then
			prompt.Enabled = enabled
		end
	end
end

function BuildService.getPad(self: Service, padId: string): BasePart?
	return self._pads[padId]
end

function BuildService.getDefenseType(self: Service, padId: string): DefenseType?
	return self._currentTypes[padId]
end

function BuildService.getUsedBudget(self: Service): number
	return self._usedBudget
end

return BuildService
