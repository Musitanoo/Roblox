--!strict

-- Defense Loop 0.1 client presentation and input.

local Players = game:GetService("Players")
local ProximityPromptService = game:GetService("ProximityPromptService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local localPlayer = Players.LocalPlayer
local playerGui = localPlayer:WaitForChild("PlayerGui")
assert(playerGui:IsA("PlayerGui"), "Local PlayerGui is required")

local replicationRoot = ReplicatedStorage:WaitForChild("Game")
assert(replicationRoot:IsA("Folder"), "ReplicatedStorage.Game must be a Folder")

local remotes = replicationRoot:WaitForChild("Remotes")
assert(remotes:IsA("Folder"), "ReplicatedStorage.Game.Remotes must be a Folder")

local requestBuild = remotes:WaitForChild("RequestBuild")
assert(requestBuild:IsA("RemoteEvent"), "RequestBuild must be a RemoteEvent")

local requestStartChallenge = remotes:WaitForChild("RequestStartChallenge")
assert(requestStartChallenge:IsA("RemoteEvent"), "RequestStartChallenge must be a RemoteEvent")

local prototype = workspace:WaitForChild("Prototype")
assert(prototype:IsA("Folder"), "Workspace.Prototype must be a Folder")

local buildPads = prototype:WaitForChild("BuildPads")
assert(buildPads:IsA("Folder"), "Prototype.BuildPads must be a Folder")

local challengeConsole = prototype:WaitForChild("ChallengeConsole")
assert(challengeConsole:IsA("BasePart"), "Prototype.ChallengeConsole must be a BasePart")

local COLORS = {
	panel = Color3.fromRGB(22, 27, 36),
	panelSecondary = Color3.fromRGB(35, 43, 56),
	text = Color3.fromRGB(245, 247, 250),
	muted = Color3.fromRGB(184, 192, 205),
	green = Color3.fromRGB(73, 190, 103),
	blue = Color3.fromRGB(40, 126, 255),
	yellow = Color3.fromRGB(255, 196, 61),
	red = Color3.fromRGB(230, 65, 65),
	gray = Color3.fromRGB(120, 128, 140),
}

local function addCorner(parent: GuiObject, radius: number)
	local corner = Instance.new("UICorner")
	corner.CornerRadius = UDim.new(0, radius)
	corner.Parent = parent
end

local function addStroke(parent: GuiObject, color: Color3, thickness: number, transparency: number)
	local stroke = Instance.new("UIStroke")
	stroke.Color = color
	stroke.Thickness = thickness
	stroke.Transparency = transparency
	stroke.Parent = parent
end

local function getHealthColor(ratio: number): Color3
	if ratio <= 0.3 then
		return COLORS.red
	end
	if ratio <= 0.6 then
		return COLORS.yellow
	end
	return COLORS.green
end

local function createLabel(parent: Instance, name: string, text: string): TextLabel
	local label = Instance.new("TextLabel")
	label.Name = name
	label.BackgroundTransparency = 1
	label.Font = Enum.Font.GothamBold
	label.Text = text
	label.TextColor3 = COLORS.text
	label.TextScaled = true
	label.TextWrapped = true
	label.Parent = parent
	return label
end

local function createButton(parent: Instance, name: string, text: string, color: Color3): TextButton
	local button = Instance.new("TextButton")
	button.Name = name
	button.AutoButtonColor = true
	button.BackgroundColor3 = color
	button.Font = Enum.Font.GothamBold
	button.Text = text
	button.TextColor3 = COLORS.text
	button.TextScaled = true
	button.TextWrapped = true
	button.Parent = parent
	addCorner(button, 8)
	addStroke(button, COLORS.text, 2, 0.62)

	local textConstraint = Instance.new("UITextSizeConstraint")
	textConstraint.MinTextSize = 11
	textConstraint.MaxTextSize = 22
	textConstraint.Parent = button
	return button
end

local screenGui = Instance.new("ScreenGui")
screenGui.Name = "DefenseLoopUI"
screenGui.IgnoreGuiInset = false
screenGui.ResetOnSpawn = false
screenGui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
screenGui.Parent = playerGui

local statusPanel = Instance.new("Frame")
statusPanel.Name = "StatusPanel"
statusPanel.AnchorPoint = Vector2.new(0.5, 0)
statusPanel.BackgroundColor3 = COLORS.panel
statusPanel.BackgroundTransparency = 0.08
statusPanel.Position = UDim2.fromScale(0.5, 0.025)
statusPanel.Size = UDim2.fromOffset(520, 92)
statusPanel.Parent = screenGui
addCorner(statusPanel, 12)
addStroke(statusPanel, COLORS.blue, 2, 0.2)

local phaseAccent = Instance.new("Frame")
phaseAccent.Name = "PhaseAccent"
phaseAccent.BackgroundColor3 = COLORS.blue
phaseAccent.BorderSizePixel = 0
phaseAccent.Size = UDim2.new(0, 7, 1, 0)
phaseAccent.Parent = statusPanel
addCorner(phaseAccent, 12)

local statusConstraint = Instance.new("UISizeConstraint")
statusConstraint.MaxSize = Vector2.new(520, 92)
statusConstraint.MinSize = Vector2.new(300, 82)
statusConstraint.Parent = statusPanel

local statusLabel = createLabel(statusPanel, "StatusLabel", "Chargement…")
statusLabel.Position = UDim2.fromOffset(12, 8)
statusLabel.Size = UDim2.new(1, -24, 1, -30)

local coreBarBack = Instance.new("Frame")
coreBarBack.Name = "CoreHealthBack"
coreBarBack.BackgroundColor3 = Color3.fromRGB(10, 13, 18)
coreBarBack.BorderSizePixel = 0
coreBarBack.Position = UDim2.new(0, 14, 1, -15)
coreBarBack.Size = UDim2.new(1, -28, 0, 7)
coreBarBack.ClipsDescendants = true
coreBarBack.Parent = statusPanel
addCorner(coreBarBack, 4)

local coreBarFill = Instance.new("Frame")
coreBarFill.Name = "Fill"
coreBarFill.BackgroundColor3 = COLORS.green
coreBarFill.BorderSizePixel = 0
coreBarFill.Size = UDim2.fromScale(1, 1)
coreBarFill.Parent = coreBarBack
addCorner(coreBarFill, 4)

local buildMenu = Instance.new("Frame")
buildMenu.Name = "BuildMenu"
buildMenu.AnchorPoint = Vector2.new(0.5, 1)
buildMenu.BackgroundColor3 = COLORS.panel
buildMenu.Position = UDim2.new(0.5, 0, 1, -24)
buildMenu.Size = UDim2.fromOffset(350, 142)
buildMenu.Visible = false
buildMenu.Parent = screenGui
addCorner(buildMenu, 12)
addStroke(buildMenu, COLORS.green, 2, 0.18)

local buildTitle = createLabel(buildMenu, "Title", "CHOISIR UNE DÉFENSE")
buildTitle.Position = UDim2.fromOffset(12, 8)
buildTitle.Size = UDim2.new(1, -24, 0, 36)

local emptyButton = createButton(buildMenu, "EmptyButton", "VIDE\nRETIRER", COLORS.gray)
emptyButton.Position = UDim2.fromOffset(12, 54)
emptyButton.Size = UDim2.fromOffset(100, 70)

local wallButton = createButton(buildMenu, "WallButton", "MUR\nBLOQUE", COLORS.green)
wallButton.Position = UDim2.fromOffset(125, 54)
wallButton.Size = UDim2.fromOffset(100, 70)

local turretButton = createButton(buildMenu, "TurretButton", "TOURELLE\nTIRE", COLORS.blue)
turretButton.Position = UDim2.fromOffset(238, 54)
turretButton.Size = UDim2.fromOffset(100, 70)

local reviewPanel = Instance.new("Frame")
reviewPanel.Name = "ReviewPanel"
reviewPanel.AnchorPoint = Vector2.new(0.5, 0.5)
reviewPanel.BackgroundColor3 = COLORS.panel
reviewPanel.Position = UDim2.fromScale(0.5, 0.52)
reviewPanel.Size = UDim2.fromOffset(360, 280)
reviewPanel.Visible = false
reviewPanel.Parent = screenGui
addCorner(reviewPanel, 14)
addStroke(reviewPanel, COLORS.blue, 3, 0.12)

local reviewTitle = createLabel(reviewPanel, "OutcomeLabel", "RÉSULTAT")
reviewTitle.Position = UDim2.fromOffset(16, 14)
reviewTitle.Size = UDim2.new(1, -32, 0, 58)

local reviewDetails = createLabel(reviewPanel, "DetailsLabel", "")
reviewDetails.Font = Enum.Font.Gotham
reviewDetails.TextColor3 = COLORS.muted
reviewDetails.Position = UDim2.fromOffset(18, 78)
reviewDetails.Size = UDim2.new(1, -36, 0, 110)

local retryButton = createButton(reviewPanel, "RetryButton", "MODIFIER ET RETENTER", COLORS.blue)
retryButton.Position = UDim2.new(0, 18, 1, -76)
retryButton.Size = UDim2.new(1, -36, 0, 58)

local selectedPad: BasePart? = nil

local function readNumberAttribute(name: string): number
	local value = replicationRoot:GetAttribute(name)
	return if typeof(value) == "number" then value else 0
end

local function readStringAttribute(name: string): string
	local value = replicationRoot:GetAttribute(name)
	return if typeof(value) == "string" then value else ""
end

local function updateInterface()
	local phase = readStringAttribute("Phase")
	local coreHealth = readNumberAttribute("CoreHealth")
	local coreMaxHealth = readNumberAttribute("CoreMaxHealth")
	local wave = readNumberAttribute("Wave")
	local totalWaves = readNumberAttribute("TotalWaves")
	local countdown = readNumberAttribute("Countdown")
	local coreRatio = if coreMaxHealth > 0 then math.clamp(coreHealth / coreMaxHealth, 0, 1) else 0
	coreBarFill.Size = UDim2.fromScale(coreRatio, 1)
	coreBarFill.BackgroundColor3 = getHealthColor(coreRatio)

	if phase == "PREPARATION" then
		phaseAccent.BackgroundColor3 = COLORS.green
		statusLabel.Text = string.format(
			"PRÉPARATION  •  NOYAU %d/%d\nConfigurez les pads verts puis utilisez la console jaune",
			coreHealth,
			coreMaxHealth
		)
	elseif phase == "STARTING" then
		phaseAccent.BackgroundColor3 = COLORS.yellow
		statusLabel.Text =
			string.format("CHALLENGE 1 DANS %d  •  CONSTRUCTION VERROUILLÉE", countdown)
	elseif phase == "DEFENDING" then
		phaseAccent.BackgroundColor3 = COLORS.red
		statusLabel.Text = string.format(
			"DÉFENSE  •  VAGUE %d/%d  •  NOYAU %d/%d",
			wave,
			totalWaves,
			coreHealth,
			coreMaxHealth
		)
	elseif phase == "VICTORY" then
		phaseAccent.BackgroundColor3 = COLORS.green
		statusLabel.Text = "VICTOIRE — ANALYSE EN COURS"
	elseif phase == "DEFEAT" then
		phaseAccent.BackgroundColor3 = COLORS.red
		statusLabel.Text = "DÉFAITE — LE NOYAU A CÉDÉ"
	elseif phase == "REVIEW" then
		phaseAccent.BackgroundColor3 = COLORS.blue
		statusLabel.Text = "AUTOPSIE DE LA DÉFENSE"
	else
		phaseAccent.BackgroundColor3 = COLORS.blue
		statusLabel.Text = "INITIALISATION DE DEFENSE LOOP 0.1"
	end

	if phase ~= "PREPARATION" then
		selectedPad = nil
		buildMenu.Visible = false
	end

	reviewPanel.Visible = phase == "REVIEW"
	statusPanel.Visible = phase ~= "REVIEW"
	if phase == "REVIEW" then
		local outcome = readStringAttribute("Outcome")
		local firstDestroyed = readStringAttribute("FirstDestroyed")
		local reachedCore = readNumberAttribute("ReachedCore")
		reviewTitle.Text = if outcome == "VICTORY" then "VICTOIRE" else "DÉFAITE"
		reviewTitle.TextColor3 = if outcome == "VICTORY" then COLORS.green else COLORS.red
		reviewDetails.Text = string.format(
			"Santé du noyau : %d/%d\nPremière structure détruite : %s\nZombies arrivés au noyau : %d",
			coreHealth,
			coreMaxHealth,
			firstDestroyed,
			reachedCore
		)
	end
end

local function selectDefense(defenseType: string)
	local pad = selectedPad
	if not pad then
		return
	end

	requestBuild:FireServer(pad.Name, defenseType)
	selectedPad = nil
	buildMenu.Visible = false
end

emptyButton.Activated:Connect(function()
	selectDefense("Empty")
end)

wallButton.Activated:Connect(function()
	selectDefense("Wall")
end)

turretButton.Activated:Connect(function()
	selectDefense("Turret")
end)

retryButton.Activated:Connect(function()
	requestStartChallenge:FireServer("ReturnToPreparation")
end)

ProximityPromptService.PromptTriggered:Connect(
	function(prompt: ProximityPrompt, playerWhoTriggered: Player)
		if playerWhoTriggered ~= localPlayer then
			return
		end

		if prompt.Name == "BuildPrompt" then
			local pad = prompt.Parent
			if pad and pad:IsA("BasePart") and pad.Parent == buildPads then
				selectedPad = pad
				buildTitle.Text = string.format("%s — CHOISISSEZ UN RÔLE", pad.Name)
				buildMenu.Visible = readStringAttribute("Phase") == "PREPARATION"
			end
		elseif prompt.Name == "StartChallengePrompt" and prompt.Parent == challengeConsole then
			requestStartChallenge:FireServer("Start")
		end
	end
)

for _, attributeName in
	{
		"Phase",
		"Countdown",
		"Wave",
		"TotalWaves",
		"CoreHealth",
		"CoreMaxHealth",
		"Outcome",
		"FirstDestroyed",
		"ReachedCore",
	}
do
	replicationRoot:GetAttributeChangedSignal(attributeName):Connect(updateInterface)
end

updateInterface()
