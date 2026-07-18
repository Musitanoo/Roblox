--!strict

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")
local Workspace = game:GetService("Workspace")

type RouteId = "Left" | "Right"
type PieceType = "Wall" | "SlowTrap" | "Turret"
type BuildPieceData = {
	id: string,
	pieceType: PieceType,
	cellX: number,
	cellZ: number,
	rotation: number,
}
type BuildPlan = { schemaVersion: number, revision: number, pieces: { [string]: BuildPieceData } }
type RouteDefenseState = {
	wallCount: number,
	wallHealth: number,
	slowTrapCount: number,
}
type StateService = {}
type StatsService = {}
type BuildService = {
	setPlanChangedCallback: (self: BuildService, callback: (BuildPlan) -> ()) -> (),
	getPlan: (self: BuildService) -> BuildPlan,
	isOwner: (self: BuildService, player: Player) -> boolean,
}
type RouteService = {
	setPlanQuery: (self: RouteService, callback: () -> BuildPlan) -> (),
	setLivePlanQuery: (self: RouteService, callback: () -> BuildPlan) -> (),
	setDefenseQuery: (self: RouteService, callback: (RouteId) -> RouteDefenseState) -> (),
}
type EnemyService = {
	setDefenseService: (self: EnemyService, defenseService: DefenseService) -> (),
}
type DefenseService = {
	setEnemyService: (self: DefenseService, enemyService: EnemyService) -> (),
	syncPlan: (self: DefenseService, plan: BuildPlan) -> (),
	getLivePlan: (self: DefenseService) -> BuildPlan,
	getRouteDefenseState: (self: DefenseService, routeId: RouteId) -> RouteDefenseState,
}
type ChallengeConfigType = { coreMaxHealth: number }
type GameStateServiceModule = {
	new: (Folder, RemoteEvent, BasePart, number) -> StateService,
}
type CombatStatsServiceModule = { new: (Folder) -> StatsService }
type BuildServiceModule = {
	new: (
		RemoteEvent,
		RemoteEvent,
		StateService,
		Folder,
		{},
		{},
		{},
		{}
	) -> BuildService,
}
type RouteServiceModule = { new: (Folder, Random?) -> RouteService }
type EnemyServiceModule = {
	new: (Folder, Folder, StateService, RouteService, StatsService) -> EnemyService,
}
type DefenseServiceModule = {
	new: (Folder, StateService, StatsService) -> DefenseService,
}
type BuildPlanStoreModule = { new: () -> {} }
type BuildHistoryModule = { new: () -> {} }
type BuildRendererModule = { new: (Folder, Folder) -> {} }
type BuildValidatorModule = { new: (Folder, {}) -> {} }
type ChallengeServiceModule = {
	new: (
		Folder,
		RemoteEvent,
		RemoteEvent,
		StateService,
		BuildService,
		RouteService,
		EnemyService,
		StatsService
	) -> {},
}

local runtimeRequire = require

local function loadModule(moduleInstance: Instance): unknown
	assert(
		moduleInstance:IsA("ModuleScript"),
		moduleInstance:GetFullName() .. " must be a ModuleScript"
	)
	return runtimeRequire(moduleInstance)
end

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

local function findOrCreateRemote(parent: Folder, name: string): RemoteEvent
	local existing = parent:FindFirstChild(name)
	if existing then
		assert(existing:IsA("RemoteEvent"), existing:GetFullName() .. " must be a RemoteEvent")
		return existing
	end
	local remote = Instance.new("RemoteEvent")
	remote.Name = name
	remote.Parent = parent
	return remote
end

local sharedGame = ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Game")
local configFolder = sharedGame:WaitForChild("Config")
local ChallengeConfig =
	loadModule(configFolder:WaitForChild("ChallengeConfig")) :: ChallengeConfigType

local gameFolder = script.Parent
assert(gameFolder and gameFolder:IsA("Folder"), "GameServer must be under Server.Game")
local servicesFolder = gameFolder:WaitForChild("Services")
local GameStateService =
	loadModule(servicesFolder:WaitForChild("GameStateService")) :: GameStateServiceModule
local BuildService =
	loadModule(servicesFolder:WaitForChild("GridBuildService")) :: BuildServiceModule
local ChallengeService =
	loadModule(servicesFolder:WaitForChild("ChallengeService")) :: ChallengeServiceModule
local RouteService =
	loadModule(servicesFolder:WaitForChild("GridRouteService")) :: RouteServiceModule
local EnemyService =
	loadModule(servicesFolder:WaitForChild("GridEnemyService")) :: EnemyServiceModule
local DefenseService =
	loadModule(servicesFolder:WaitForChild("GridDefenseService")) :: DefenseServiceModule
local CombatStatsService =
	loadModule(servicesFolder:WaitForChild("CombatStatsService")) :: CombatStatsServiceModule
local buildFolder = gameFolder:WaitForChild("Build")
local BuildPlanStore =
	loadModule(buildFolder:WaitForChild("BuildPlanStore")) :: BuildPlanStoreModule
local BuildHistory = loadModule(buildFolder:WaitForChild("BuildHistory")) :: BuildHistoryModule
local BuildRenderer = loadModule(buildFolder:WaitForChild("BuildRenderer")) :: BuildRendererModule
local BuildValidator =
	loadModule(buildFolder:WaitForChild("BuildValidator")) :: BuildValidatorModule

local prototype = Workspace:WaitForChild("Prototype", 10)
assert(prototype and prototype:IsA("Folder"), "Workspace.Prototype is required")
local objectiveCore = prototype:FindFirstChild("ObjectiveCore")
assert(objectiveCore and objectiveCore:IsA("BasePart"), "Prototype.ObjectiveCore is required")
local templates = ServerStorage:WaitForChild("GameTemplates", 10)
assert(templates and templates:IsA("Folder"), "ServerStorage.GameTemplates is required")

local replicationRoot = findOrCreateFolder(ReplicatedStorage, "Game")
replicationRoot:SetAttribute("Ready", false)
local remotes = findOrCreateFolder(replicationRoot, "Remotes")
local buildRequest = findOrCreateRemote(remotes, "BuildRequest")
local buildResult = findOrCreateRemote(remotes, "BuildResult")
local requestStart = findOrCreateRemote(remotes, "RequestStartChallenge")
local requestReturn = findOrCreateRemote(remotes, "RequestReturnToPreparation")
local stateChanged = findOrCreateRemote(remotes, "StateChanged")

local stateService = GameStateService.new(
	replicationRoot,
	stateChanged,
	objectiveCore,
	ChallengeConfig.coreMaxHealth
)
local statsService = CombatStatsService.new(replicationRoot)
local routeService = RouteService.new(prototype, nil)
local buildPlanStore = BuildPlanStore.new()
local buildHistory = BuildHistory.new()
local buildRenderer = BuildRenderer.new(prototype, templates)
local buildValidator = BuildValidator.new(prototype, buildRenderer)
local buildService = BuildService.new(
	buildRequest,
	buildResult,
	stateService,
	replicationRoot,
	buildPlanStore,
	buildHistory,
	buildRenderer,
	buildValidator
)
local enemyService =
	EnemyService.new(prototype, templates, stateService, routeService, statsService)
local defenseService = DefenseService.new(prototype, stateService, statsService)

buildService:setPlanChangedCallback(function(plan: BuildPlan)
	defenseService:syncPlan(plan)
end)
routeService:setPlanQuery(function(): BuildPlan
	return buildService:getPlan()
end)
routeService:setLivePlanQuery(function(): BuildPlan
	return defenseService:getLivePlan()
end)
routeService:setDefenseQuery(function(routeId: RouteId): RouteDefenseState
	return defenseService:getRouteDefenseState(routeId)
end)
enemyService:setDefenseService(defenseService)
defenseService:setEnemyService(enemyService)

local challengeService = ChallengeService.new(
	prototype,
	requestStart,
	requestReturn,
	stateService,
	buildService,
	routeService,
	enemyService,
	statsService
)

replicationRoot:SetAttribute("Version", "Build Loop 0.3")
replicationRoot:SetAttribute("ServiceCount", if challengeService then 7 else 0)
replicationRoot:SetAttribute("Ready", true)
print("Build Loop 0.3 server ready")
