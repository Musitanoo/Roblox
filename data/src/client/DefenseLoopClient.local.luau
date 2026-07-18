--!strict

local Players = game:GetService("Players")
local ProximityPromptService = game:GetService("ProximityPromptService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

type Colors = {
	panel: Color3,
	panelSecondary: Color3,
	text: Color3,
	muted: Color3,
	green: Color3,
	blue: Color3,
	yellow: Color3,
	red: Color3,
	gray: Color3,
}
type HUD = {
	showMessage: (self: HUD, message: string, isError: boolean) -> (),
	update: (self: HUD) -> (),
	getLaunchButton: (self: HUD) -> TextButton,
}
type Build = {
	update: (self: Build) -> (),
}
type Review = { update: (self: Review) -> () }
type HUDModule = { new: (ScreenGui, Folder, Colors) -> HUD }
type BuildModule = {
	new: (
		ScreenGui,
		Folder,
		RemoteEvent,
		RemoteEvent,
		Folder,
		Colors,
		(string, boolean) -> ()
	) -> Build,
}
type ReviewModule = {
	new: (ScreenGui, Folder, RemoteEvent, Colors, (string, boolean) -> ()) -> Review,
}

local localPlayer = Players.LocalPlayer
local playerGui = localPlayer:WaitForChild("PlayerGui")
assert(playerGui:IsA("PlayerGui"), "Local PlayerGui is required")

local replicationRoot = ReplicatedStorage:WaitForChild("Game")
assert(replicationRoot:IsA("Folder"), "ReplicatedStorage.Game must be a Folder")
while replicationRoot:GetAttribute("Ready") ~= true do
	replicationRoot:GetAttributeChangedSignal("Ready"):Wait()
end
local remotes = replicationRoot:WaitForChild("Remotes")
assert(remotes:IsA("Folder"), "ReplicatedStorage.Game.Remotes must be a Folder")
local buildRequest = remotes:WaitForChild("BuildRequest")
local buildResult = remotes:WaitForChild("BuildResult")
local requestStart = remotes:WaitForChild("RequestStartChallenge")
local requestReturn = remotes:WaitForChild("RequestReturnToPreparation")
local stateChanged = remotes:WaitForChild("StateChanged")
assert(buildRequest:IsA("RemoteEvent"), "BuildRequest must be a RemoteEvent")
assert(buildResult:IsA("RemoteEvent"), "BuildResult must be a RemoteEvent")
assert(requestStart:IsA("RemoteEvent"), "RequestStartChallenge must be a RemoteEvent")
assert(requestReturn:IsA("RemoteEvent"), "RequestReturnToPreparation must be a RemoteEvent")
assert(stateChanged:IsA("RemoteEvent"), "StateChanged must be a RemoteEvent")

local prototype = workspace:WaitForChild("Prototype")
assert(prototype:IsA("Folder"), "Workspace.Prototype must be a Folder")
local challengeConsole = prototype:WaitForChild("ChallengeConsole")
assert(challengeConsole:IsA("BasePart"), "Prototype.ChallengeConsole must be a BasePart")

local scriptParent = script.Parent
assert(scriptParent, "DefenseLoopClient requires a parent")
local controllerFolder = scriptParent:WaitForChild("GameClient")
assert(controllerFolder:IsA("Folder"), "Client.GameClient must be a Folder")
local hudModule = controllerFolder:WaitForChild("HUDController")
local buildModule = controllerFolder:WaitForChild("GridBuildController")
local reviewModule = controllerFolder:WaitForChild("ReviewController")
assert(hudModule:IsA("ModuleScript"), "HUDController must be a ModuleScript")
assert(buildModule:IsA("ModuleScript"), "GridBuildController must be a ModuleScript")
assert(reviewModule:IsA("ModuleScript"), "ReviewController must be a ModuleScript")
local runtimeRequire = require
local BuildController = runtimeRequire(buildModule) :: BuildModule
local HUDController = runtimeRequire(hudModule) :: HUDModule
local ReviewController = runtimeRequire(reviewModule) :: ReviewModule

local existing = playerGui:FindFirstChild("DefenseLoopUI")
if existing then
	existing:Destroy()
end
local screenGui = Instance.new("ScreenGui")
screenGui.Name = "DefenseLoopUI"
screenGui.IgnoreGuiInset = false
screenGui.ResetOnSpawn = false
screenGui.DisplayOrder = 10
screenGui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
screenGui.Parent = playerGui

local colors = table.freeze({
	panel = Color3.fromRGB(20, 26, 36),
	panelSecondary = Color3.fromRGB(34, 43, 57),
	text = Color3.fromRGB(245, 247, 250),
	muted = Color3.fromRGB(180, 191, 207),
	green = Color3.fromRGB(65, 193, 108),
	blue = Color3.fromRGB(48, 135, 255),
	yellow = Color3.fromRGB(255, 190, 55),
	red = Color3.fromRGB(235, 70, 66),
	gray = Color3.fromRGB(111, 123, 140),
})

local hud = HUDController.new(screenGui, replicationRoot, colors)
local function showMessage(message: string, isError: boolean)
	hud:showMessage(message, isError)
end
local build = BuildController.new(
	screenGui,
	replicationRoot,
	buildRequest,
	buildResult,
	prototype,
	colors,
	showMessage
)
local review = ReviewController.new(screenGui, replicationRoot, requestReturn, colors, showMessage)

local function updateInterface()
	hud:update()
	build:update()
	review:update()
end

local function isLocalOwner(): boolean
	return replicationRoot:GetAttribute("BuildOwnerUserId") == localPlayer.UserId
end

local launchButton = hud:getLaunchButton()
launchButton.Activated:Connect(function()
	if isLocalOwner() and replicationRoot:GetAttribute("Phase") == "PREPARATION" then
		requestStart:FireServer()
	end
end)
requestStart.OnClientEvent:Connect(function(accepted: unknown, message: unknown)
	if typeof(accepted) == "boolean" and typeof(message) == "string" then
		showMessage(message, not accepted)
	end
end)

ProximityPromptService.PromptTriggered:Connect(
	function(prompt: ProximityPrompt, playerWhoTriggered: Player)
		if playerWhoTriggered ~= localPlayer then
			return
		end
		if prompt.Name == "StartPrompt" and prompt.Parent == challengeConsole then
			if isLocalOwner() and replicationRoot:GetAttribute("Phase") == "PREPARATION" then
				requestStart:FireServer()
			end
		end
	end
)

for _, attributeName in ipairs({
	"Phase",
	"Countdown",
	"Wave",
	"TotalWaves",
	"EnemiesRemaining",
	"BruteWarning",
	"CoreHealth",
	"CoreMaxHealth",
	"StructureUsed",
	"StructureMax",
	"PowerUsed",
	"PowerMax",
	"BuildOwnerUserId",
	"BuildRevision",
	"BuildEnabled",
	"ReportReady",
	"Result",
	"ChallengeDuration",
	"CoreHealthRemaining",
	"LeftLaneEnemyCount",
	"RightLaneEnemyCount",
	"LeftLaneCoreHits",
	"RightLaneCoreHits",
	"FirstBreachTime",
	"FirstBreachLane",
	"FirstBreachPadId",
	"FirstBreachEnemyType",
	"TotalWallDamageAbsorbed",
	"TotalTurretDamage",
	"TotalEnemiesSlowed",
}) do
	replicationRoot:GetAttributeChangedSignal(attributeName):Connect(updateInterface)
end
stateChanged.OnClientEvent:Connect(updateInterface)
updateInterface()
