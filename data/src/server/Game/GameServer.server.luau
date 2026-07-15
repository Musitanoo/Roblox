--!strict

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")
local Workspace = game:GetService("Workspace")

type OpaqueStateService = {}
type OpaqueBuildService = {}
type OpaqueEnemyService = {}
type ChallengeConfigType = {
	coreMaxHealth: number,
}
type GameStateServiceModule = {
	new: (replicaRoot: Folder, core: BasePart, coreMaxHealth: number) -> OpaqueStateService,
}
type BuildServiceModule = {
	new: (
		prototype: Folder,
		templates: Folder,
		requestBuild: RemoteEvent,
		stateService: OpaqueStateService
	) -> OpaqueBuildService,
}
type EnemyServiceModule = {
	new: (
		prototype: Folder,
		templates: Folder,
		stateService: OpaqueStateService
	) -> OpaqueEnemyService,
}
type ChallengeServiceModule = {
	new: (
		prototype: Folder,
		requestStartChallenge: RemoteEvent,
		stateService: OpaqueStateService,
		buildService: OpaqueBuildService,
		enemyService: OpaqueEnemyService
	) -> {},
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

local gameFolder = script.Parent
assert(gameFolder and gameFolder:IsA("Folder"), "GameServer must be parented to the Game folder")
local servicesFolder = gameFolder:WaitForChild("Services")

local BuildService = loadModule(servicesFolder:WaitForChild("BuildService")) :: BuildServiceModule
local ChallengeService =
	loadModule(servicesFolder:WaitForChild("ChallengeService")) :: ChallengeServiceModule
local EnemyService = loadModule(servicesFolder:WaitForChild("EnemyService")) :: EnemyServiceModule
local GameStateService =
	loadModule(servicesFolder:WaitForChild("GameStateService")) :: GameStateServiceModule

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

local function findOrCreateRemote(parent: Folder, name: string): RemoteEvent
	local existing = parent:FindFirstChild(name)
	if existing then
		assert(
			existing:IsA("RemoteEvent"),
			string.format("%s must be a RemoteEvent", existing:GetFullName())
		)
		return existing
	end

	local remote = Instance.new("RemoteEvent")
	remote.Name = name
	remote.Parent = parent
	return remote
end

local prototype = Workspace:WaitForChild("Prototype", 10)
assert(prototype and prototype:IsA("Folder"), "Workspace.Prototype is required")

local objectiveCore = prototype:FindFirstChild("ObjectiveCore")
assert(objectiveCore and objectiveCore:IsA("BasePart"), "Prototype.ObjectiveCore is required")

local templates = ServerStorage:WaitForChild("GameTemplates", 10)
assert(templates and templates:IsA("Folder"), "ServerStorage.GameTemplates is required")

local replicationRoot = findOrCreateFolder(ReplicatedStorage, "Game")
local remotes = findOrCreateFolder(replicationRoot, "Remotes")
local requestBuild = findOrCreateRemote(remotes, "RequestBuild")
local requestStartChallenge = findOrCreateRemote(remotes, "RequestStartChallenge")

local stateService =
	GameStateService.new(replicationRoot, objectiveCore, ChallengeConfig.coreMaxHealth)
local buildService = BuildService.new(prototype, templates, requestBuild, stateService)
local enemyService = EnemyService.new(prototype, templates, stateService)
local challengeService =
	ChallengeService.new(prototype, requestStartChallenge, stateService, buildService, enemyService)

replicationRoot:SetAttribute("Version", "Defense Loop 0.1")
replicationRoot:SetAttribute("Ready", true)
replicationRoot:SetAttribute("ServiceCount", if challengeService then 4 else 0)

print("Defense Loop 0.1 server ready")
