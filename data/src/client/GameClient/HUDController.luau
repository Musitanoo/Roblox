--!strict

local Players = game:GetService("Players")

type Colors = {
	panel: Color3,
	panelSecondary: Color3,
	text: Color3,
	muted: Color3,
	green: Color3,
	blue: Color3,
	yellow: Color3,
	red: Color3,
}

local HUDController = {}
HUDController.__index = HUDController

export type Controller = typeof(setmetatable(
	{} :: {
		_replicationRoot: Folder,
		_colors: Colors,
		_statusPanel: Frame,
		_statusLabel: TextLabel,
		_coreFill: Frame,
		_preparationPanel: Frame,
		_launchButton: TextButton,
		_warning: TextLabel,
		_toast: TextLabel,
		_toastToken: number,
	},
	HUDController
))

local function addCorner(parent: GuiObject, radius: number)
	local corner = Instance.new("UICorner")
	corner.CornerRadius = UDim.new(0, radius)
	corner.Parent = parent
end

local function addStroke(parent: GuiObject, color: Color3, thickness: number)
	local stroke = Instance.new("UIStroke")
	stroke.Color = color
	stroke.Thickness = thickness
	stroke.Transparency = 0.25
	stroke.Parent = parent
end

local function textLabel(parent: Instance, name: string, text: string): TextLabel
	local label = Instance.new("TextLabel")
	label.Name = name
	label.BackgroundTransparency = 1
	label.Font = Enum.Font.GothamBold
	label.Text = text
	label.TextColor3 = Color3.fromRGB(245, 247, 250)
	label.TextScaled = true
	label.TextWrapped = true
	label.Parent = parent
	local constraint = Instance.new("UITextSizeConstraint")
	constraint.MinTextSize = 11
	constraint.MaxTextSize = 22
	constraint.Parent = label
	return label
end

local function readNumber(root: Folder, name: string): number
	local value = root:GetAttribute(name)
	return if typeof(value) == "number" then value else 0
end

local function readString(root: Folder, name: string): string
	local value = root:GetAttribute(name)
	return if typeof(value) == "string" then value else ""
end

function HUDController.new(
	screenGui: ScreenGui,
	replicationRoot: Folder,
	colors: Colors
): Controller
	local statusPanel = Instance.new("Frame")
	statusPanel.Name = "StatusPanel"
	statusPanel.AnchorPoint = Vector2.new(0.5, 0)
	statusPanel.BackgroundColor3 = colors.panel
	statusPanel.BackgroundTransparency = 0.05
	statusPanel.Position = UDim2.new(0.5, 0, 0, 10)
	statusPanel.Size = UDim2.new(0.92, 0, 0, 82)
	statusPanel.Parent = screenGui
	addCorner(statusPanel, 12)
	addStroke(statusPanel, colors.blue, 2)
	local statusSize = Instance.new("UISizeConstraint")
	statusSize.MinSize = Vector2.new(290, 76)
	statusSize.MaxSize = Vector2.new(620, 86)
	statusSize.Parent = statusPanel

	local statusLabel = textLabel(statusPanel, "StatusLabel", "INITIALISATION")
	statusLabel.Position = UDim2.fromOffset(12, 7)
	statusLabel.Size = UDim2.new(1, -24, 1, -24)

	local coreBack = Instance.new("Frame")
	coreBack.Name = "CoreBack"
	coreBack.BackgroundColor3 = Color3.fromRGB(8, 12, 18)
	coreBack.BorderSizePixel = 0
	coreBack.ClipsDescendants = true
	coreBack.Position = UDim2.new(0, 12, 1, -14)
	coreBack.Size = UDim2.new(1, -24, 0, 7)
	coreBack.Parent = statusPanel
	addCorner(coreBack, 4)
	local coreFill = Instance.new("Frame")
	coreFill.Name = "Fill"
	coreFill.BackgroundColor3 = colors.green
	coreFill.BorderSizePixel = 0
	coreFill.Size = UDim2.fromScale(1, 1)
	coreFill.Parent = coreBack
	addCorner(coreFill, 4)

	local preparationPanel = Instance.new("Frame")
	preparationPanel.Name = "ChallengeCard"
	preparationPanel.AnchorPoint = Vector2.new(0.5, 1)
	preparationPanel.BackgroundColor3 = colors.panel
	preparationPanel.BackgroundTransparency = 0.04
	preparationPanel.Position = UDim2.new(0.5, 0, 1, -16)
	preparationPanel.Size = UDim2.new(0.94, 0, 0, 122)
	preparationPanel.Parent = screenGui
	addCorner(preparationPanel, 12)
	addStroke(preparationPanel, colors.yellow, 2)
	local preparationSize = Instance.new("UISizeConstraint")
	preparationSize.MinSize = Vector2.new(300, 112)
	preparationSize.MaxSize = Vector2.new(680, 128)
	preparationSize.Parent = preparationPanel

	local challengeText = textLabel(
		preparationPanel,
		"ChallengeText",
		"CHALLENGE 2 — PREMIÈRE BRÈCHE\n2 routes • Rôdeurs + Brutes\nLes Brutes recherchent les routes les plus fortifiées et brisent vite les Murs."
	)
	challengeText.TextXAlignment = Enum.TextXAlignment.Left
	challengeText.Position = UDim2.fromOffset(14, 8)
	challengeText.Size = UDim2.new(0.68, -18, 1, -16)

	local launchButton = Instance.new("TextButton")
	launchButton.Name = "LaunchButton"
	launchButton.AnchorPoint = Vector2.new(1, 0.5)
	launchButton.BackgroundColor3 = colors.yellow
	launchButton.Position = UDim2.new(1, -12, 0.5, 0)
	launchButton.Size = UDim2.new(0.31, 0, 0, 76)
	launchButton.Font = Enum.Font.GothamBold
	launchButton.Text = "LANCER\nCHALLENGE 2"
	launchButton.TextColor3 = Color3.fromRGB(22, 27, 36)
	launchButton.TextScaled = true
	launchButton.TextWrapped = true
	launchButton.Parent = preparationPanel
	addCorner(launchButton, 10)
	local launchTextSize = Instance.new("UITextSizeConstraint")
	launchTextSize.MinTextSize = 12
	launchTextSize.MaxTextSize = 21
	launchTextSize.Parent = launchButton

	local warning = textLabel(screenGui, "BruteWarning", "")
	warning.AnchorPoint = Vector2.new(0.5, 0.5)
	warning.BackgroundColor3 = colors.red
	warning.BackgroundTransparency = 0.06
	warning.Position = UDim2.fromScale(0.5, 0.25)
	warning.Size = UDim2.new(0.88, 0, 0, 64)
	warning.Visible = false
	addCorner(warning, 12)
	addStroke(warning, Color3.fromRGB(255, 190, 150), 3)
	local warningSize = Instance.new("UISizeConstraint")
	warningSize.MaxSize = Vector2.new(620, 68)
	warningSize.Parent = warning

	local toast = textLabel(screenGui, "Toast", "")
	toast.AnchorPoint = Vector2.new(0.5, 0)
	toast.BackgroundColor3 = colors.panelSecondary
	toast.BackgroundTransparency = 0.03
	toast.Position = UDim2.new(0.5, 0, 0, 100)
	toast.Size = UDim2.new(0.75, 0, 0, 42)
	toast.Visible = false
	toast.ZIndex = 20
	addCorner(toast, 9)
	local toastSize = Instance.new("UISizeConstraint")
	toastSize.MaxSize = Vector2.new(500, 44)
	toastSize.Parent = toast

	return setmetatable({
		_replicationRoot = replicationRoot,
		_colors = colors,
		_statusPanel = statusPanel,
		_statusLabel = statusLabel,
		_coreFill = coreFill,
		_preparationPanel = preparationPanel,
		_launchButton = launchButton,
		_warning = warning,
		_toast = toast,
		_toastToken = 0,
	}, HUDController)
end

function HUDController.getLaunchButton(self: Controller): TextButton
	return self._launchButton
end

function HUDController.showMessage(self: Controller, message: string, isError: boolean)
	self._toastToken += 1
	local token = self._toastToken
	self._toast.Text = string.sub(message, 1, 80)
	self._toast.TextColor3 = if isError then self._colors.red else self._colors.green
	self._toast.Visible = true
	task.delay(2.2, function()
		if self._toastToken == token then
			self._toast.Visible = false
		end
	end)
end

function HUDController.update(self: Controller)
	local phase = readString(self._replicationRoot, "Phase")
	local isOwner = self._replicationRoot:GetAttribute("BuildOwnerUserId")
		== Players.LocalPlayer.UserId
	local viewport = if workspace.CurrentCamera
		then workspace.CurrentCamera.ViewportSize
		else Vector2.new(1280, 720)
	if viewport.X < 900 or viewport.Y < 500 then
		self._preparationPanel.AnchorPoint = Vector2.new(1, 1)
		self._preparationPanel.Position = UDim2.new(1, -8, 1, -8)
		self._preparationPanel.Size = UDim2.fromOffset(480, 106)
	else
		self._preparationPanel.AnchorPoint = Vector2.new(0.5, 1)
		self._preparationPanel.Position = UDim2.new(0.5, 0, 1, -16)
		self._preparationPanel.Size = UDim2.new(0.94, 0, 0, 122)
	end
	local coreHealth = readNumber(self._replicationRoot, "CoreHealth")
	local coreMax = readNumber(self._replicationRoot, "CoreMaxHealth")
	local ratio = if coreMax > 0 then math.clamp(coreHealth / coreMax, 0, 1) else 0
	self._coreFill.Size = UDim2.fromScale(ratio, 1)
	self._coreFill.BackgroundColor3 = if ratio <= 0.3
		then self._colors.red
		elseif ratio <= 0.6 then self._colors.yellow
		else self._colors.green

	self._preparationPanel.Visible = phase == "PREPARATION"
	self._launchButton.Active = phase == "PREPARATION" and isOwner
	self._launchButton.Selectable = self._launchButton.Active
	self._launchButton.AutoButtonColor = self._launchButton.Active
	self._launchButton.BackgroundColor3 = if isOwner
		then self._colors.yellow
		else self._colors.muted
	self._launchButton.Text = if isOwner then "LANCER\nCHALLENGE 2" else "MODE\nOBSERVATION"
	self._statusPanel.Visible = phase ~= "REVIEW"
	if phase == "PREPARATION" then
		self._statusLabel.Text = string.format(
			"PRÉPARATION • STRUCTURE %d/%d • ÉNERGIE %d/%d • NOYAU %d/%d",
			readNumber(self._replicationRoot, "StructureUsed"),
			readNumber(self._replicationRoot, "StructureMax"),
			readNumber(self._replicationRoot, "PowerUsed"),
			readNumber(self._replicationRoot, "PowerMax"),
			coreHealth,
			coreMax
		)
	elseif phase == "STARTING" then
		self._statusLabel.Text = string.format(
			"DÉPART DANS %d • CONSTRUCTION VERROUILLÉE",
			readNumber(self._replicationRoot, "Countdown")
		)
	elseif phase == "DEFENDING" then
		self._statusLabel.Text = string.format(
			"VAGUE %d/%d • NOYAU %d/%d • %d ENNEMIS",
			readNumber(self._replicationRoot, "Wave"),
			readNumber(self._replicationRoot, "TotalWaves"),
			coreHealth,
			coreMax,
			readNumber(self._replicationRoot, "EnemiesRemaining")
		)
	elseif phase == "VICTORY" then
		self._statusLabel.Text = "VICTOIRE • AUTOPSIE EN COURS"
	elseif phase == "DEFEAT" then
		self._statusLabel.Text = "DÉFAITE • AUTOPSIE EN COURS"
	else
		self._statusLabel.Text = "BUILD LOOP 0.3"
	end

	local warningText = readString(self._replicationRoot, "BruteWarning")
	self._warning.Text = warningText
	self._warning.Visible = phase == "DEFENDING" and warningText ~= ""
end

return HUDController
