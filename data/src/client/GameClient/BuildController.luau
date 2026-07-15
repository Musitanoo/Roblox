--!strict

type Colors = {
	panel: Color3,
	text: Color3,
	muted: Color3,
	green: Color3,
	blue: Color3,
	yellow: Color3,
	red: Color3,
	gray: Color3,
}
type MessageCallback = (message: string, isError: boolean) -> ()

local BuildController = {}
BuildController.__index = BuildController

export type Controller = typeof(setmetatable(
	{} :: {
		_replicationRoot: Folder,
		_requestBuild: RemoteEvent,
		_menu: Frame,
		_title: TextLabel,
		_challengeCard: GuiObject?,
		_selectedPad: BasePart?,
		_messageCallback: MessageCallback,
	},
	BuildController
))

local function addCorner(parent: GuiObject, radius: number)
	local corner = Instance.new("UICorner")
	corner.CornerRadius = UDim.new(0, radius)
	corner.Parent = parent
end

local function makeButton(
	parent: Instance,
	name: string,
	text: string,
	color: Color3,
	position: UDim2
): TextButton
	local button = Instance.new("TextButton")
	button.Name = name
	button.BackgroundColor3 = color
	button.Position = position
	button.Size = UDim2.new(0.235, 0, 0, 68)
	button.Font = Enum.Font.GothamBold
	button.Text = text
	button.TextColor3 = Color3.fromRGB(245, 247, 250)
	button.TextScaled = true
	button.TextWrapped = true
	button.Parent = parent
	addCorner(button, 9)
	local constraint = Instance.new("UITextSizeConstraint")
	constraint.MinTextSize = 10
	constraint.MaxTextSize = 19
	constraint.Parent = button
	return button
end

function BuildController.new(
	screenGui: ScreenGui,
	replicationRoot: Folder,
	requestBuild: RemoteEvent,
	colors: Colors,
	messageCallback: MessageCallback
): Controller
	local menu = Instance.new("Frame")
	menu.Name = "BuildMenu"
	menu.AnchorPoint = Vector2.new(0.5, 1)
	menu.BackgroundColor3 = colors.panel
	menu.BackgroundTransparency = 0.02
	menu.Position = UDim2.new(0.5, 0, 1, -16)
	menu.Size = UDim2.new(0.94, 0, 0, 122)
	menu.Visible = false
	menu.ZIndex = 10
	menu.Parent = screenGui
	addCorner(menu, 12)
	local stroke = Instance.new("UIStroke")
	stroke.Color = colors.green
	stroke.Thickness = 2
	stroke.Parent = menu
	local size = Instance.new("UISizeConstraint")
	size.MinSize = Vector2.new(300, 118)
	size.MaxSize = Vector2.new(620, 126)
	size.Parent = menu

	local title = Instance.new("TextLabel")
	title.Name = "Title"
	title.BackgroundTransparency = 1
	title.Position = UDim2.fromOffset(10, 5)
	title.Size = UDim2.new(1, -20, 0, 36)
	title.Font = Enum.Font.GothamBold
	title.Text = "CHOISIR UNE DÉFENSE"
	title.TextColor3 = colors.text
	title.TextScaled = true
	title.Parent = menu
	local titleSize = Instance.new("UITextSizeConstraint")
	titleSize.MinTextSize = 11
	titleSize.MaxTextSize = 20
	titleSize.Parent = title

	local empty =
		makeButton(menu, "EmptyButton", "VIDE\n0 PT", colors.gray, UDim2.new(0.015, 0, 0, 45))
	local wall =
		makeButton(menu, "WallButton", "MUR\n1 PT", colors.green, UDim2.new(0.26, 0, 0, 45))
	local trap = makeButton(
		menu,
		"SlowTrapButton",
		"PIÈGE\n1 PT",
		colors.yellow,
		UDim2.new(0.505, 0, 0, 45)
	)
	local turret =
		makeButton(menu, "TurretButton", "TOURELLE\n2 PT", colors.blue, UDim2.new(0.75, 0, 0, 45))

	local self: Controller = setmetatable({
		_replicationRoot = replicationRoot,
		_requestBuild = requestBuild,
		_menu = menu,
		_title = title,
		_challengeCard = screenGui:FindFirstChild("ChallengeCard") :: GuiObject?,
		_selectedPad = nil,
		_messageCallback = messageCallback,
	}, BuildController)

	local function choose(defenseType: string)
		self:_choose(defenseType)
	end
	empty.Activated:Connect(function()
		choose("Empty")
	end)
	wall.Activated:Connect(function()
		choose("Wall")
	end)
	trap.Activated:Connect(function()
		choose("SlowTrap")
	end)
	turret.Activated:Connect(function()
		choose("Turret")
	end)
	requestBuild.OnClientEvent:Connect(function(accepted: unknown, message: unknown)
		if typeof(accepted) == "boolean" and typeof(message) == "string" then
			messageCallback(message, not accepted)
		end
	end)
	return self
end

function BuildController.open(self: Controller, pad: BasePart)
	if self._replicationRoot:GetAttribute("Phase") ~= "PREPARATION" then
		return
	end
	self._selectedPad = pad
	if self._challengeCard then
		self._challengeCard.Visible = false
	end
	local current = pad:GetAttribute("DefenseType")
	self._title.Text = string.format("%s • ACTUEL : %s", pad.Name, tostring(current or "Empty"))
	self._menu.Visible = true
end

function BuildController.close(self: Controller)
	self._selectedPad = nil
	self._menu.Visible = false
	if self._challengeCard then
		self._challengeCard.Visible = self._replicationRoot:GetAttribute("Phase") == "PREPARATION"
	end
end

function BuildController._choose(self: Controller, defenseType: string)
	local pad = self._selectedPad
	if not pad then
		return
	end
	self._requestBuild:FireServer(pad.Name, defenseType)
	self:close()
end

function BuildController.update(self: Controller)
	if self._replicationRoot:GetAttribute("Phase") ~= "PREPARATION" then
		self:close()
	end
end

return BuildController
