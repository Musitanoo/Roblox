--!strict

local Players = game:GetService("Players")

type Colors = {
	panel: Color3,
	panelSecondary: Color3,
	text: Color3,
	muted: Color3,
	green: Color3,
	blue: Color3,
	red: Color3,
}
type MessageCallback = (message: string, isError: boolean) -> ()

local ReviewController = {}
ReviewController.__index = ReviewController

export type Controller = typeof(setmetatable(
	{} :: {
		_replicationRoot: Folder,
		_panel: Frame,
		_resultCard: TextLabel,
		_trafficCard: TextLabel,
		_breachCard: TextLabel,
		_defenseCard: TextLabel,
		_retryButton: TextButton,
	},
	ReviewController
))

local function addCorner(parent: GuiObject, radius: number)
	local corner = Instance.new("UICorner")
	corner.CornerRadius = UDim.new(0, radius)
	corner.Parent = parent
end

local function readNumber(root: Folder, name: string): number
	local value = root:GetAttribute(name)
	return if typeof(value) == "number" then value else 0
end

local function readString(root: Folder, name: string): string
	local value = root:GetAttribute(name)
	return if typeof(value) == "string" then value else ""
end

local function makeCard(parent: Instance, name: string, position: UDim2, colors: Colors): TextLabel
	local card = Instance.new("TextLabel")
	card.Name = name
	card.BackgroundColor3 = colors.panelSecondary
	card.BackgroundTransparency = 0.04
	card.Position = position
	card.Size = UDim2.fromScale(0.475, 0.27)
	card.Font = Enum.Font.Gotham
	card.Text = ""
	card.TextColor3 = colors.text
	card.TextScaled = true
	card.TextWrapped = true
	card.Parent = parent
	addCorner(card, 10)
	local constraint = Instance.new("UITextSizeConstraint")
	constraint.MinTextSize = 10
	constraint.MaxTextSize = 18
	constraint.Parent = card
	return card
end

function ReviewController.new(
	screenGui: ScreenGui,
	replicationRoot: Folder,
	requestReturn: RemoteEvent,
	colors: Colors,
	messageCallback: MessageCallback
): Controller
	local panel = Instance.new("Frame")
	panel.Name = "ReviewPanel"
	panel.AnchorPoint = Vector2.new(0.5, 0.5)
	panel.BackgroundColor3 = colors.panel
	panel.BackgroundTransparency = 0.02
	panel.Position = UDim2.fromScale(0.5, 0.5)
	panel.Size = UDim2.new(0.94, 0, 1, -12)
	panel.Visible = false
	panel.Parent = screenGui
	addCorner(panel, 14)
	local stroke = Instance.new("UIStroke")
	stroke.Color = colors.blue
	stroke.Thickness = 3
	stroke.Parent = panel
	local size = Instance.new("UISizeConstraint")
	size.MinSize = Vector2.new(300, 280)
	size.MaxSize = Vector2.new(700, 520)
	size.Parent = panel

	local title = Instance.new("TextLabel")
	title.Name = "Title"
	title.BackgroundTransparency = 1
	title.Position = UDim2.fromOffset(14, 8)
	title.Size = UDim2.new(1, -28, 0, 42)
	title.Font = Enum.Font.GothamBold
	title.Text = "AUTOPSIE FACTUELLE"
	title.TextColor3 = colors.text
	title.TextScaled = true
	title.Parent = panel

	local resultCard = makeCard(panel, "ResultCard", UDim2.fromScale(0.015, 0.14), colors)
	local trafficCard = makeCard(panel, "TrafficCard", UDim2.fromScale(0.51, 0.14), colors)
	local breachCard = makeCard(panel, "FirstBreachCard", UDim2.fromScale(0.015, 0.45), colors)
	local defenseCard = makeCard(panel, "DefenseCard", UDim2.fromScale(0.51, 0.45), colors)

	local retry = Instance.new("TextButton")
	retry.Name = "ModifyBaseButton"
	retry.AnchorPoint = Vector2.new(0.5, 1)
	retry.BackgroundColor3 = colors.blue
	retry.Position = UDim2.new(0.5, 0, 1, -10)
	retry.Size = UDim2.new(0.68, 0, 0, 50)
	retry.Font = Enum.Font.GothamBold
	retry.Text = "MODIFIER LA BASE"
	retry.TextColor3 = colors.text
	retry.TextScaled = true
	retry.Parent = panel
	addCorner(retry, 10)

	local self: Controller = setmetatable({
		_replicationRoot = replicationRoot,
		_panel = panel,
		_resultCard = resultCard,
		_trafficCard = trafficCard,
		_breachCard = breachCard,
		_defenseCard = defenseCard,
		_retryButton = retry,
	}, ReviewController)
	retry.Activated:Connect(function()
		if
			replicationRoot:GetAttribute("Phase") == "REVIEW"
			and replicationRoot:GetAttribute("BuildOwnerUserId") == Players.LocalPlayer.UserId
		then
			requestReturn:FireServer()
		end
	end)
	requestReturn.OnClientEvent:Connect(function(accepted: unknown, message: unknown)
		if typeof(accepted) == "boolean" and typeof(message) == "string" then
			messageCallback(message, not accepted)
		end
	end)
	return self
end

function ReviewController.update(self: Controller)
	local phase = readString(self._replicationRoot, "Phase")
	local isOwner = self._replicationRoot:GetAttribute("BuildOwnerUserId")
		== Players.LocalPlayer.UserId
	self._panel.Visible = phase == "REVIEW"
	self._retryButton.Active = phase == "REVIEW" and isOwner
	self._retryButton.Selectable = self._retryButton.Active
	self._retryButton.AutoButtonColor = self._retryButton.Active
	self._retryButton.Text = if isOwner then "MODIFIER LA BASE" else "MODE OBSERVATION"
	if phase ~= "REVIEW" then
		return
	end
	local result = readString(self._replicationRoot, "Result")
	local coreHealth = readNumber(self._replicationRoot, "CoreHealthRemaining")
	local coreMax = readNumber(self._replicationRoot, "CoreMaxHealth")
	local duration = readNumber(self._replicationRoot, "ChallengeDuration")
	self._resultCard.Text = string.format(
		"RÉSULTAT\n%s\nNoyau : %d/%d\nDurée : %.1f s",
		if result == "VICTORY" then "VICTOIRE" else "DÉFAITE",
		coreHealth,
		coreMax,
		duration
	)

	local left = readNumber(self._replicationRoot, "LeftLaneEnemyCount")
	local right = readNumber(self._replicationRoot, "RightLaneEnemyCount")
	local total = left + right
	local leftPercent = if total > 0 then math.floor(left / total * 100 + 0.5) else 0
	local rightPercent = if total > 0 then 100 - leftPercent else 0
	self._trafficCard.Text = string.format(
		"TRAFIC\nGauche : %d%% (%d)\nDroite : %d%% (%d)\nImpacts noyau : %d / %d",
		leftPercent,
		left,
		rightPercent,
		right,
		readNumber(self._replicationRoot, "LeftLaneCoreHits"),
		readNumber(self._replicationRoot, "RightLaneCoreHits")
	)

	local breachPad = readString(self._replicationRoot, "FirstBreachPadId")
	if breachPad == "" then
		self._breachCard.Text = "PREMIÈRE BRÈCHE\nAucun Mur détruit"
	else
		self._breachCard.Text = string.format(
			"PREMIÈRE BRÈCHE\n%s • %s\n%.1f s\nCause : %s",
			readString(self._replicationRoot, "FirstBreachLane"),
			breachPad,
			readNumber(self._replicationRoot, "FirstBreachTime"),
			readString(self._replicationRoot, "FirstBreachEnemyType")
		)
	end

	self._defenseCard.Text = string.format(
		"DÉFENSES\nTourelles : %.0f dégâts\nMurs : %.0f absorbés\nEnnemis ralentis : %d",
		readNumber(self._replicationRoot, "TotalTurretDamage"),
		readNumber(self._replicationRoot, "TotalWallDamageAbsorbed"),
		readNumber(self._replicationRoot, "TotalEnemiesSlowed")
	)
end

return ReviewController
