--!strict

local ContextActionService = game:GetService("ContextActionService")
local HttpService = game:GetService("HttpService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local UserInputService = game:GetService("UserInputService")

type PieceType = "Wall" | "SlowTrap" | "Turret"
type BuildPieceData = {
	id: string,
	pieceType: PieceType,
	cellX: number,
	cellZ: number,
	rotation: number,
}
type BuildPlan = { schemaVersion: number, revision: number, pieces: { [string]: BuildPieceData } }
type BuildRulesModule = {
	ValidatePiece: (BuildPlan, BuildPieceData, string?) -> (boolean, string?),
}
type GridMathModule = {
	WorldToCell: (CFrame, Vector3) -> (number, number),
	CellToWorld: (CFrame, number, number) -> Vector3,
	GetPieceWorldCFrame: (CFrame, BuildPieceData) -> CFrame,
	GetFootprint: (PieceType, number) -> (number, number),
}
type RouteSolverModule = {
	Solve: (
		BuildPlan,
		"Left" | "Right",
		"Roamer" | "Brute"
	) -> ({ { x: number, z: number } }?, number),
}
type GridConfig = {
	schemaVersion: number,
	width: number,
	depth: number,
	cellSize: number,
	buildSurfaceName: string,
}
type PieceTuning = { structureCost: number, powerCost: number, queryHeight: number }
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
type MessageCallback = (string, boolean) -> ()

local sharedGame = ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Game")
local config = sharedGame:WaitForChild("Config")
local BuildGridConfig =
	require(config:WaitForChild("BuildGridConfig") :: ModuleScript) :: GridConfig
local BuildRules =
	require(sharedGame:WaitForChild("BuildRules") :: ModuleScript) :: BuildRulesModule
local GridMath = require(sharedGame:WaitForChild("GridMath") :: ModuleScript) :: GridMathModule
local PieceConfig =
	require(config:WaitForChild("PieceConfig") :: ModuleScript) :: { [PieceType]: PieceTuning }
local RouteSolver =
	require(sharedGame:WaitForChild("RouteSolver") :: ModuleScript) :: RouteSolverModule

local GridBuildController = {}
GridBuildController.__index = GridBuildController

export type Controller = typeof(setmetatable(
	{} :: {
		_replicationRoot: Folder,
		_buildRequest: RemoteEvent,
		_surface: BasePart,
		_runtimeDefenses: Folder,
		_colors: Colors,
		_messageCallback: MessageCallback,
		_panel: Frame,
		_info: TextLabel,
		_confirmButton: TextButton,
		_moveButton: TextButton,
		_deleteButton: TextButton,
		_zoomOutButton: TextButton,
		_zoomInButton: TextButton,
		_plan: BuildPlan,
		_selectedType: PieceType,
		_rotation: number,
		_selectedPieceId: string?,
		_movingPieceId: string?,
		_cellX: number,
		_cellZ: number,
		_ghost: Model,
		_pathPreview: Folder,
		_requestSession: string,
		_requestSerial: number,
		_pendingCount: number,
		_valid: boolean,
		_lastPreviewKey: string,
		_cameraActive: boolean,
		_savedCameraType: Enum.CameraType?,
		_savedCameraCFrame: CFrame?,
		_cameraCenter: Vector3,
		_zoom: number,
		_keys: { [Enum.KeyCode]: boolean },
		_touchStart: Vector2?,
		_touchLast: Vector2?,
		_touchDragged: boolean,
		_pinching: boolean,
		_pinchLastScale: number,
		_placementActive: boolean,
	},
	GridBuildController
))

local function addCorner(parent: GuiObject, radius: number)
	local corner = Instance.new("UICorner")
	corner.CornerRadius = UDim.new(0, radius)
	corner.Parent = parent
end

local function makeButton(parent: Instance, name: string, text: string, color: Color3): TextButton
	local button = Instance.new("TextButton")
	button.Name = name
	button.BackgroundColor3 = color
	button.Size = UDim2.new(1, 0, 0, 46)
	button.Font = Enum.Font.GothamBold
	button.Text = text
	button.TextColor3 = Color3.fromRGB(245, 247, 250)
	button.TextScaled = true
	button.TextWrapped = true
	button.AutoButtonColor = true
	button.Parent = parent
	addCorner(button, 8)
	local constraint = Instance.new("UITextSizeConstraint")
	constraint.MinTextSize = 10
	constraint.MaxTextSize = 17
	constraint.Parent = button
	return button
end

local function readPlan(value: unknown): BuildPlan?
	if typeof(value) ~= "table" then
		return nil
	end
	local valueTable = value :: { [string]: unknown }
	if typeof(valueTable.revision) ~= "number" or typeof(valueTable.pieces) ~= "table" then
		return nil
	end
	return value :: BuildPlan
end

local function reasonMessage(reason: unknown): string
	local messages: { [string]: string } = {
		OUTSIDE_GRID = "Hors grille",
		FORBIDDEN_CELL = "Zone réservée à la route ou au noyau",
		OCCUPIED = "Cellule occupée",
		WORLD_OVERLAP = "Obstacle du monde",
		STRUCTURE_LIMIT = "Limite Structure atteinte",
		POWER_LIMIT = "Limite Énergie atteinte",
		INVALID_PIECE = "Pièce invalide",
		INVALID_ROTATION = "Rotation interdite",
		NOT_OWNER = "Mode observation : seul le propriétaire construit",
		WRONG_STATE = "Construction verrouillée pendant le challenge",
		STALE_REVISION = "Plan resynchronisé après une modification concurrente",
		RATE_LIMITED = "Trop de demandes",
		REQUEST_CONFLICT = "Action indisponible",
	}
	return if typeof(reason) == "string" then messages[reason] or reason else "Action refusée"
end

local function findBuildModel(instance: Instance?): Model?
	local current = instance
	while current do
		if current:IsA("Model") and typeof(current:GetAttribute("PieceId")) == "string" then
			return current
		end
		current = current.Parent
	end
	return nil
end

function GridBuildController.new(
	screenGui: ScreenGui,
	replicationRoot: Folder,
	buildRequest: RemoteEvent,
	buildResult: RemoteEvent,
	prototype: Folder,
	colors: Colors,
	messageCallback: MessageCallback
): Controller
	local surface = prototype:WaitForChild(BuildGridConfig.buildSurfaceName)
	local runtime = prototype:WaitForChild("Runtime")
	local defenses = runtime:WaitForChild("Defenses")
	assert(
		surface:IsA("BasePart"),
		"Prototype." .. BuildGridConfig.buildSurfaceName .. " must be a BasePart"
	)
	assert(defenses:IsA("Folder"), "Prototype.Runtime.Defenses must be a Folder")

	local panel = Instance.new("Frame")
	panel.Name = "GridBuildPanel"
	panel.BackgroundColor3 = colors.panel
	panel.BackgroundTransparency = 0.03
	panel.Position = UDim2.fromOffset(12, 82)
	panel.Size = UDim2.fromOffset(228, 260)
	panel.Parent = screenGui
	addCorner(panel, 12)
	local size = Instance.new("UISizeConstraint")
	size.MinSize = Vector2.new(190, 250)
	size.MaxSize = Vector2.new(228, 260)
	size.Parent = panel
	local padding = Instance.new("UIPadding")
	padding.PaddingTop = UDim.new(0, 7)
	padding.PaddingBottom = UDim.new(0, 7)
	padding.PaddingLeft = UDim.new(0, 7)
	padding.PaddingRight = UDim.new(0, 7)
	padding.Parent = panel
	local layout = Instance.new("UIListLayout")
	layout.Padding = UDim.new(0, 4)
	layout.Parent = panel

	local info = Instance.new("TextLabel")
	info.Name = "BuildInfo"
	info.BackgroundColor3 = colors.panelSecondary
	info.Size = UDim2.new(1, 0, 0, 44)
	info.Font = Enum.Font.GothamBold
	info.TextColor3 = colors.text
	info.TextScaled = true
	info.TextWrapped = true
	info.LayoutOrder = 1
	info.Parent = panel
	addCorner(info, 8)
	local infoConstraint = Instance.new("UITextSizeConstraint")
	infoConstraint.MinTextSize = 9
	infoConstraint.MaxTextSize = 15
	infoConstraint.Parent = info

	local function makeRow(name: string): Frame
		local row = Instance.new("Frame")
		row.Name = name
		row.BackgroundTransparency = 1
		row.Size = UDim2.new(1, 0, 0, 44)
		row.Parent = panel
		local rowLayout = Instance.new("UIListLayout")
		rowLayout.FillDirection = Enum.FillDirection.Horizontal
		rowLayout.HorizontalAlignment = Enum.HorizontalAlignment.Center
		rowLayout.Padding = UDim.new(0, 4)
		rowLayout.Parent = row
		return row
	end

	local pieceRow = makeRow("PieceRow")
	pieceRow.LayoutOrder = 2
	local function pieceLabel(label: string, pieceType: PieceType): string
		local tuning = PieceConfig[pieceType]
		return string.format("%s\nS%d E%d", label, tuning.structureCost, tuning.powerCost)
	end
	local wall = makeButton(pieceRow, "WallButton", pieceLabel("MUR", "Wall"), colors.green)
	local trap = makeButton(pieceRow, "TrapButton", pieceLabel("PIÈGE", "SlowTrap"), colors.yellow)
	local turret =
		makeButton(pieceRow, "TurretButton", pieceLabel("TOURELLE", "Turret"), colors.blue)
	for _, button in ipairs({ wall, trap, turret }) do
		button.Size = UDim2.new(1 / 3, -3, 1, 0)
	end

	local controlRow = makeRow("ControlRow")
	controlRow.LayoutOrder = 3
	local rotate = makeButton(controlRow, "RotateButton", "TOURNER\nR / X", colors.gray)
	local confirm = makeButton(controlRow, "ConfirmButton", "CONFIRMER\nA", colors.green)
	rotate.Size = UDim2.new(0.42, -2, 1, 0)
	confirm.Size = UDim2.new(0.58, -2, 1, 0)

	local selectionRow = makeRow("SelectionRow")
	selectionRow.LayoutOrder = 4
	local move = makeButton(selectionRow, "MoveButton", "DÉPLACER", colors.blue)
	local delete = makeButton(selectionRow, "DeleteButton", "SUPPRIMER\nY", colors.red)
	local zoomOut = makeButton(selectionRow, "ZoomOutButton", "ZOOM -", colors.gray)
	local zoomIn = makeButton(selectionRow, "ZoomInButton", "ZOOM +", colors.gray)
	move.Size = UDim2.new(0.55, -2, 1, 0)
	delete.Size = UDim2.new(0.45, -2, 1, 0)
	zoomOut.Size = UDim2.new(0.5, -2, 1, 0)
	zoomIn.Size = UDim2.new(0.5, -2, 1, 0)

	local historyRow = Instance.new("Frame")
	historyRow.Name = "HistoryRow"
	historyRow.BackgroundTransparency = 1
	historyRow.Size = UDim2.new(1, 0, 0, 44)
	historyRow.LayoutOrder = 5
	historyRow.Parent = panel
	local rowLayout = Instance.new("UIListLayout")
	rowLayout.FillDirection = Enum.FillDirection.Horizontal
	rowLayout.Padding = UDim.new(0, 5)
	rowLayout.Parent = historyRow
	local undo = makeButton(historyRow, "UndoButton", "↶", colors.gray)
	local redo = makeButton(historyRow, "RedoButton", "↷", colors.gray)
	local clear = makeButton(historyRow, "ClearButton", "VIDER", colors.red)
	undo.Size = UDim2.fromScale(0.24, 1)
	redo.Size = UDim2.fromScale(0.24, 1)
	clear.Size = UDim2.new(0.48, -5, 1, 0)

	local ghost = Instance.new("Model")
	ghost.Name = "BuildGhost"
	local ghostPart = Instance.new("Part")
	ghostPart.Name = "GhostVolume"
	ghostPart.Anchored = true
	ghostPart.CanCollide = false
	ghostPart.CanQuery = false
	ghostPart.CanTouch = false
	ghostPart.Material = Enum.Material.ForceField
	ghostPart.Transparency = 0.38
	ghostPart.Parent = ghost
	ghost.PrimaryPart = ghostPart
	local highlight = Instance.new("Highlight")
	highlight.Name = "Validity"
	highlight.FillTransparency = 0.72
	highlight.OutlineTransparency = 0
	highlight.Parent = ghost

	local pathPreview = Instance.new("Folder")
	pathPreview.Name = "RoutePreview"

	local self: Controller = setmetatable({
		_replicationRoot = replicationRoot,
		_buildRequest = buildRequest,
		_surface = surface,
		_runtimeDefenses = defenses,
		_colors = colors,
		_messageCallback = messageCallback,
		_panel = panel,
		_info = info,
		_confirmButton = confirm,
		_moveButton = move,
		_deleteButton = delete,
		_zoomOutButton = zoomOut,
		_zoomInButton = zoomIn,
		_plan = { schemaVersion = BuildGridConfig.schemaVersion, revision = 0, pieces = {} },
		_selectedType = "Wall" :: PieceType,
		_rotation = 0,
		_selectedPieceId = nil :: string?,
		_movingPieceId = nil :: string?,
		_cellX = 1,
		_cellZ = 1,
		_ghost = ghost,
		_pathPreview = pathPreview,
		_requestSession = HttpService:GenerateGUID(false),
		_requestSerial = 0,
		_pendingCount = 0,
		_valid = false,
		_lastPreviewKey = "",
		_cameraActive = false,
		_savedCameraType = nil,
		_savedCameraCFrame = nil,
		_cameraCenter = surface.Position,
		_zoom = 72,
		_keys = {},
		_touchStart = nil,
		_touchLast = nil,
		_touchDragged = false,
		_pinching = false,
		_pinchLastScale = 1,
		_placementActive = true,
	}, GridBuildController)

	wall.Activated:Connect(function()
		self:_selectType("Wall")
	end)
	trap.Activated:Connect(function()
		self:_selectType("SlowTrap")
	end)
	turret.Activated:Connect(function()
		self:_selectType("Turret")
	end)
	rotate.Activated:Connect(function()
		self:rotate()
	end)
	confirm.Activated:Connect(function()
		self:confirm()
	end)
	move.Activated:Connect(function()
		self:beginMove()
	end)
	delete.Activated:Connect(function()
		self:deleteSelection()
	end)
	zoomOut.Activated:Connect(function()
		self:adjustZoom(8)
	end)
	zoomIn.Activated:Connect(function()
		self:adjustZoom(-8)
	end)
	undo.Activated:Connect(function()
		self:_send("UNDO", {})
	end)
	redo.Activated:Connect(function()
		self:_send("REDO", {})
	end)
	clear.Activated:Connect(function()
		self:_send("CLEAR_ALL", {})
	end)

	buildResult.OnClientEvent:Connect(function(value: unknown)
		self:_receive(value)
	end)
	UserInputService.InputBegan:Connect(function(input: InputObject, gameProcessed: boolean)
		if gameProcessed then
			return
		end
		if input.UserInputType == Enum.UserInputType.MouseButton2 then
			self:cancel()
			return
		end
		self._keys[input.KeyCode] = true
		if input.UserInputType == Enum.UserInputType.Touch and self:_canBuild() then
			local position = Vector2.new(input.Position.X, input.Position.Y)
			self._touchStart = position
			self._touchLast = position
			self._touchDragged = false
		end
	end)
	UserInputService.InputEnded:Connect(function(input: InputObject, gameProcessed: boolean)
		self._keys[input.KeyCode] = nil
		if input.UserInputType == Enum.UserInputType.Touch then
			local shouldSelect = not gameProcessed and not self._touchDragged and self:_canBuild()
			self._touchStart = nil
			self._touchLast = nil
			self._touchDragged = false
			if shouldSelect then
				self:_pointAt(input.Position.X, input.Position.Y, true)
			end
			return
		end
		if gameProcessed or not self:_canBuild() then
			return
		end
		if input.UserInputType == Enum.UserInputType.MouseButton1 then
			self:_pointAt(input.Position.X, input.Position.Y, true)
		end
	end)
	UserInputService.InputChanged:Connect(function(input: InputObject, gameProcessed: boolean)
		if gameProcessed or not self:_canBuild() then
			return
		end
		if input.UserInputType == Enum.UserInputType.Touch then
			local position = Vector2.new(input.Position.X, input.Position.Y)
			local start = self._touchStart
			local previous = self._touchLast
			if start and previous and not self._pinching then
				if (position - start).Magnitude >= 12 then
					self._touchDragged = true
				end
				if self._touchDragged then
					local camera = workspace.CurrentCamera
					if camera then
						local delta = position - previous
						local groundRight =
							Vector3.new(camera.CFrame.RightVector.X, 0, camera.CFrame.RightVector.Z)
						local groundUp =
							Vector3.new(camera.CFrame.UpVector.X, 0, camera.CFrame.UpVector.Z)
						local scale = self._zoom / 620
						if groundRight.Magnitude > 0 then
							self._cameraCenter -= groundRight.Unit * delta.X * scale
						end
						if groundUp.Magnitude > 0 then
							self._cameraCenter += groundUp.Unit * delta.Y * scale
						end
					end
				end
			end
			self._touchLast = position
		elseif input.UserInputType == Enum.UserInputType.MouseMovement then
			self:_pointAt(input.Position.X, input.Position.Y, false)
		elseif input.UserInputType == Enum.UserInputType.MouseWheel then
			self._zoom = math.clamp(self._zoom - input.Position.Z * 5, 48, 100)
		end
	end)
	UserInputService.TouchPinch:Connect(
		function(
			_positions,
			scale: number,
			_velocity,
			state: Enum.UserInputState,
			processed: boolean
		)
			if not self:_canBuild() then
				return
			end
			if not processed and state == Enum.UserInputState.Change then
				local scaleDelta = scale / math.max(self._pinchLastScale, 0.01)
				self._zoom = math.clamp(self._zoom / math.clamp(scaleDelta, 0.8, 1.2), 48, 100)
				self._pinchLastScale = scale
				self._touchDragged = true
			elseif state == Enum.UserInputState.Begin then
				self._pinching = true
				self._pinchLastScale = scale
				self._touchDragged = true
			elseif state == Enum.UserInputState.End then
				self._pinching = false
				self._pinchLastScale = 1
			end
		end
	)

	ContextActionService:BindAction("BuildConfirm", function(_, state)
		if not self:_canBuild() then
			return Enum.ContextActionResult.Pass
		end
		if state == Enum.UserInputState.Begin then
			self:confirm()
		end
		return Enum.ContextActionResult.Sink
	end, false, Enum.KeyCode.ButtonA, Enum.KeyCode.Return)
	ContextActionService:BindAction("BuildRotate", function(_, state)
		if not self:_canBuild() then
			return Enum.ContextActionResult.Pass
		end
		if state == Enum.UserInputState.Begin then
			self:rotate()
		end
		return Enum.ContextActionResult.Sink
	end, false, Enum.KeyCode.ButtonX, Enum.KeyCode.R)
	ContextActionService:BindAction("BuildDelete", function(_, state)
		if not self:_canBuild() then
			return Enum.ContextActionResult.Pass
		end
		if state == Enum.UserInputState.Begin then
			self:deleteSelection()
		end
		return Enum.ContextActionResult.Sink
	end, false, Enum.KeyCode.ButtonY, Enum.KeyCode.Delete)
	ContextActionService:BindAction("BuildCancel", function(_, state)
		if not self:_canBuild() then
			return Enum.ContextActionResult.Pass
		end
		if state == Enum.UserInputState.Begin then
			self:cancel()
		end
		return Enum.ContextActionResult.Sink
	end, false, Enum.KeyCode.ButtonB, Enum.KeyCode.Escape)
	ContextActionService:BindAction("BuildCursorLeft", function(_, state)
		if not self:_canBuild() then
			return Enum.ContextActionResult.Pass
		end
		if state == Enum.UserInputState.Begin then
			self:moveCursor(-1, 0)
		end
		return Enum.ContextActionResult.Sink
	end, false, Enum.KeyCode.DPadLeft)
	ContextActionService:BindAction("BuildCursorRight", function(_, state)
		if not self:_canBuild() then
			return Enum.ContextActionResult.Pass
		end
		if state == Enum.UserInputState.Begin then
			self:moveCursor(1, 0)
		end
		return Enum.ContextActionResult.Sink
	end, false, Enum.KeyCode.DPadRight)
	ContextActionService:BindAction("BuildCursorUp", function(_, state)
		if not self:_canBuild() then
			return Enum.ContextActionResult.Pass
		end
		if state == Enum.UserInputState.Begin then
			self:moveCursor(0, -1)
		end
		return Enum.ContextActionResult.Sink
	end, false, Enum.KeyCode.DPadUp)
	ContextActionService:BindAction("BuildCursorDown", function(_, state)
		if not self:_canBuild() then
			return Enum.ContextActionResult.Pass
		end
		if state == Enum.UserInputState.Begin then
			self:moveCursor(0, 1)
		end
		return Enum.ContextActionResult.Sink
	end, false, Enum.KeyCode.DPadDown)
	ContextActionService:BindAction("BuildZoomIn", function(_, state)
		if not self:_canBuild() then
			return Enum.ContextActionResult.Pass
		end
		if state == Enum.UserInputState.Begin then
			self:adjustZoom(-8)
		end
		return Enum.ContextActionResult.Sink
	end, false, Enum.KeyCode.ButtonR2)
	ContextActionService:BindAction("BuildZoomOut", function(_, state)
		if not self:_canBuild() then
			return Enum.ContextActionResult.Pass
		end
		if state == Enum.UserInputState.Begin then
			self:adjustZoom(8)
		end
		return Enum.ContextActionResult.Sink
	end, false, Enum.KeyCode.ButtonL2)
	ContextActionService:BindAction("BuildUndo", function(_, state)
		if not self:_canBuild() then
			return Enum.ContextActionResult.Pass
		end
		if state == Enum.UserInputState.Begin then
			self:_send("UNDO", {})
		end
		return Enum.ContextActionResult.Sink
	end, false, Enum.KeyCode.ButtonL1, Enum.KeyCode.Z)
	ContextActionService:BindAction("BuildRedo", function(_, state)
		if not self:_canBuild() then
			return Enum.ContextActionResult.Pass
		end
		if state == Enum.UserInputState.Begin then
			self:_send("REDO", {})
		end
		return Enum.ContextActionResult.Sink
	end, false, Enum.KeyCode.ButtonR1, Enum.KeyCode.Y)

	RunService.RenderStepped:Connect(function(deltaTime: number)
		self:_render(deltaTime)
	end)
	self:_reconstructPlan()
	self:update()
	return self
end

function GridBuildController._canBuild(self: Controller): boolean
	return self._replicationRoot:GetAttribute("Phase") == "PREPARATION"
		and self._replicationRoot:GetAttribute("BuildEnabled") == true
		and self._replicationRoot:GetAttribute("BuildOwnerUserId") == Players.LocalPlayer.UserId
end

function GridBuildController._reconstructPlan(self: Controller)
	local pieces: { [string]: BuildPieceData } = {}
	for _, child in self._runtimeDefenses:GetChildren() do
		if child:IsA("Model") then
			local id = child:GetAttribute("PieceId")
			local pieceType = child:GetAttribute("PieceType")
			local cellX = child:GetAttribute("CellX")
			local cellZ = child:GetAttribute("CellZ")
			local rotation = child:GetAttribute("Rotation")
			if
				typeof(id) == "string"
				and (pieceType == "Wall" or pieceType == "SlowTrap" or pieceType == "Turret")
				and typeof(cellX) == "number"
				and typeof(cellZ) == "number"
				and typeof(rotation) == "number"
			then
				pieces[id] = {
					id = id,
					pieceType = pieceType,
					cellX = cellX,
					cellZ = cellZ,
					rotation = rotation,
				}
			end
		end
	end
	self._plan = {
		schemaVersion = BuildGridConfig.schemaVersion,
		revision = self._replicationRoot:GetAttribute("BuildRevision") :: number? or 0,
		pieces = pieces,
	}
end

function GridBuildController._receive(self: Controller, value: unknown)
	if typeof(value) ~= "table" then
		return
	end
	local valueTable = value :: { [string]: unknown }
	local delta = valueTable.delta
	local deltaTable = if typeof(delta) == "table" then delta :: { [string]: unknown } else nil
	local plan = if deltaTable then readPlan(deltaTable.plan) else nil
	if valueTable.requestId ~= "SYNC" then
		self._pendingCount = if valueTable.reason == "RATE_LIMITED"
			then 0
			else math.max(0, self._pendingCount - 1)
	end
	if plan and plan.revision >= self._plan.revision then
		self._plan = plan
		self._lastPreviewKey = ""
	end
	if valueTable.success == false then
		self._messageCallback(reasonMessage(valueTable.reason), true)
	elseif valueTable.requestId ~= "SYNC" then
		self._messageCallback("Plan mis à jour", false)
	end
	self._selectedPieceId = nil
	self._movingPieceId = nil
	self:update()
end

function GridBuildController._send(
	self: Controller,
	operation: string,
	payload: { [string]: unknown }
)
	if not self:_canBuild() then
		self._messageCallback("Construction indisponible", true)
		return
	end
	self._requestSerial += 1
	self._pendingCount += 1
	self._buildRequest:FireServer({
		requestId = string.format("%s:%d", self._requestSession, self._requestSerial),
		baseRevision = self._plan.revision,
		operation = operation,
		payload = payload,
	})
end

function GridBuildController._selectType(self: Controller, pieceType: PieceType)
	if not self:_canBuild() then
		return
	end
	self._selectedType = pieceType
	self._rotation = 0
	self._selectedPieceId = nil
	self._movingPieceId = nil
	self._placementActive = true
	self:update()
end

function GridBuildController.cancel(self: Controller)
	if not self:_canBuild() then
		return
	end
	self._selectedPieceId = nil
	self._movingPieceId = nil
	self._placementActive = false
	self._messageCallback("Opération annulée", false)
	self:update()
end

function GridBuildController.moveCursor(self: Controller, deltaX: number, deltaZ: number)
	if not self:_canBuild() then
		return
	end
	if self._selectedPieceId and not self._movingPieceId then
		return
	end
	local nextCellX = math.clamp(self._cellX + deltaX, 1, BuildGridConfig.width)
	local nextCellZ = math.clamp(self._cellZ + deltaZ, 1, BuildGridConfig.depth)
	if nextCellX == self._cellX and nextCellZ == self._cellZ then
		return
	end
	self._cellX = nextCellX
	self._cellZ = nextCellZ
	self._placementActive = true
	self._selectedPieceId = nil
end

function GridBuildController.adjustZoom(self: Controller, delta: number)
	if self:_canBuild() then
		self._zoom = math.clamp(self._zoom + delta, 48, 100)
	end
end

function GridBuildController.rotate(self: Controller)
	if not self:_canBuild() then
		return
	end
	if self._selectedPieceId and not self._movingPieceId then
		local piece = self._plan.pieces[self._selectedPieceId]
		if piece and piece.pieceType ~= "SlowTrap" then
			self:_send("ROTATE", { pieceId = piece.id, rotation = (piece.rotation + 1) % 4 })
		end
		return
	end
	if self._selectedType ~= "SlowTrap" then
		self._rotation = (self._rotation + 1) % 4
	end
end

function GridBuildController.confirm(self: Controller)
	if not self:_canBuild() or not self._placementActive or not self._valid then
		return
	end
	if self._movingPieceId then
		self:_send(
			"MOVE",
			{ pieceId = self._movingPieceId, cellX = self._cellX, cellZ = self._cellZ }
		)
	else
		self:_send("PLACE", {
			pieceType = self._selectedType,
			cellX = self._cellX,
			cellZ = self._cellZ,
			rotation = self._rotation,
		})
	end
end

function GridBuildController.beginMove(self: Controller)
	if not self:_canBuild() then
		return
	end
	local id = self._selectedPieceId
	local piece = if id then self._plan.pieces[id] else nil
	if piece then
		self._movingPieceId = piece.id
		self._selectedPieceId = nil
		self._selectedType = piece.pieceType
		self._rotation = piece.rotation
		self._cellX = piece.cellX
		self._cellZ = piece.cellZ
		self._placementActive = true
		self:update()
	end
end

function GridBuildController.deleteSelection(self: Controller)
	if self._selectedPieceId then
		self:_send("DELETE", { pieceId = self._selectedPieceId })
	end
end

function GridBuildController._pointAt(self: Controller, x: number, y: number, selectModel: boolean)
	if not selectModel and not self._placementActive then
		return
	end
	local camera = workspace.CurrentCamera
	if not camera then
		return
	end
	local ray = camera:ViewportPointToRay(x, y)
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Exclude
	local excluded: { Instance } = { self._ghost, self._pathPreview }
	if Players.LocalPlayer.Character then
		table.insert(excluded, Players.LocalPlayer.Character)
	end
	params.FilterDescendantsInstances = excluded
	local hit = workspace:Raycast(ray.Origin, ray.Direction * 500, params)
	if not hit then
		return
	end
	if selectModel then
		local model = findBuildModel(hit.Instance)
		if model and model:IsDescendantOf(self._runtimeDefenses) then
			local pieceId = model:GetAttribute("PieceId")
			if typeof(pieceId) == "string" and self._plan.pieces[pieceId] then
				self._selectedPieceId = pieceId
				self._movingPieceId = nil
				self._placementActive = false
				self:update()
				return
			end
		end
	end
	local cellX, cellZ = GridMath.WorldToCell(self._surface.CFrame, hit.Position)
	local selectionChanged = self._selectedPieceId ~= nil or not self._placementActive
	if
		cellX == self._cellX
		and cellZ == self._cellZ
		and not selectionChanged
		and self._movingPieceId == nil
	then
		return
	end
	self._cellX = cellX
	self._cellZ = cellZ
	self._selectedPieceId = nil
	self._placementActive = true
	if selectionChanged then
		self:update()
	end
end

function GridBuildController._previewPlan(self: Controller, piece: BuildPieceData): BuildPlan
	local pieces = table.clone(self._plan.pieces)
	if self._movingPieceId then
		pieces[self._movingPieceId] = nil
	end
	pieces[piece.id] = piece
	return {
		schemaVersion = self._plan.schemaVersion,
		revision = self._plan.revision,
		pieces = pieces,
	}
end

function GridBuildController._drawPaths(self: Controller, plan: BuildPlan)
	for _, child in self._pathPreview:GetChildren() do
		child:Destroy()
	end
	local routeData: { { routeId: "Left" | "Right", color: Color3 } } = {
		{ routeId = "Left", color = self._colors.blue },
		{ routeId = "Right", color = self._colors.yellow },
	}
	for _, route in routeData do
		local cells = RouteSolver.Solve(plan, route.routeId, "Roamer")
		if cells then
			for _, cell in cells do
				local marker = Instance.new("Part")
				marker.Name = "PathCell"
				marker.Anchored = true
				marker.CanCollide = false
				marker.CanQuery = false
				marker.CanTouch = false
				marker.Material = Enum.Material.Neon
				marker.Color = route.color
				marker.Transparency = 0.55
				marker.Size = Vector3.new(1.25, 0.12, 1.25)
				local world = GridMath.CellToWorld(self._surface.CFrame, cell.x, cell.z)
				marker.CFrame = CFrame.new(world + Vector3.new(0, 0.12, 0))
				marker.Parent = self._pathPreview
			end
		end
	end
end

function GridBuildController._renderGhost(self: Controller)
	local ghostPart = self._ghost.PrimaryPart
	local highlight = self._ghost:FindFirstChild("Validity")
	if not ghostPart or not highlight or not highlight:IsA("Highlight") then
		return
	end
	local id = self._movingPieceId or "GHOST"
	local piece: BuildPieceData = {
		id = id,
		pieceType = self._selectedType,
		cellX = self._cellX,
		cellZ = self._cellZ,
		rotation = self._rotation,
	}
	local previewKey = string.format(
		"%d:%s:%d:%s:%d:%d:%d",
		self._plan.revision,
		self._movingPieceId or "",
		piece.cellX,
		piece.pieceType,
		piece.cellZ,
		piece.rotation,
		self._pendingCount
	)
	if previewKey == self._lastPreviewKey then
		return
	end
	self._lastPreviewKey = previewKey
	local valid, reason = BuildRules.ValidatePiece(self._plan, piece, self._movingPieceId)
	self._valid = valid
	local color = if valid then self._colors.green else self._colors.red
	ghostPart.Color = color
	highlight.FillColor = color
	highlight.OutlineColor = color
	local width, depth = GridMath.GetFootprint(piece.pieceType, 0)
	local height = PieceConfig[piece.pieceType].queryHeight
	ghostPart.Size = Vector3.new(
		width * BuildGridConfig.cellSize - 0.35,
		height,
		depth * BuildGridConfig.cellSize - 0.35
	)
	ghostPart.CFrame = GridMath.GetPieceWorldCFrame(self._surface.CFrame, piece)
		* CFrame.new(0, height * 0.5, 0)
	local placementStatus = if self._pendingCount > 0
		then "EN ATTENTE SERVEUR"
		else if valid then "Placement valide" else reasonMessage(reason)
	self._info.Text = string.format(
		"%s • (%d,%d) • R%d\n%s",
		piece.pieceType,
		piece.cellX,
		piece.cellZ,
		piece.rotation * 90,
		placementStatus
	)
	self:_drawPaths(self:_previewPlan(piece))
end

function GridBuildController._updateCamera(self: Controller, deltaTime: number)
	local camera = workspace.CurrentCamera
	if not camera then
		return
	end
	local shouldActivate = self:_canBuild()
	if shouldActivate and not self._cameraActive then
		self._savedCameraType = camera.CameraType
		self._savedCameraCFrame = camera.CFrame
		camera.CameraType = Enum.CameraType.Scriptable
		self._cameraActive = true
	elseif not shouldActivate and self._cameraActive then
		camera.CameraType = self._savedCameraType or Enum.CameraType.Custom
		if self._savedCameraCFrame then
			camera.CFrame = self._savedCameraCFrame
		end
		self._cameraActive = false
	end
	if not self._cameraActive then
		return
	end
	local pan = Vector3.zero
	if self._keys[Enum.KeyCode.W] or self._keys[Enum.KeyCode.Up] then
		pan += Vector3.new(0, 0, -1)
	end
	if self._keys[Enum.KeyCode.S] or self._keys[Enum.KeyCode.Down] then
		pan += Vector3.new(0, 0, 1)
	end
	if self._keys[Enum.KeyCode.A] or self._keys[Enum.KeyCode.Left] then
		pan += Vector3.new(-1, 0, 0)
	end
	if self._keys[Enum.KeyCode.D] or self._keys[Enum.KeyCode.Right] then
		pan += Vector3.new(1, 0, 0)
	end
	if pan.Magnitude > 0 then
		self._cameraCenter += pan.Unit * 24 * deltaTime
	end
	local localCenter = self._surface.CFrame:PointToObjectSpace(self._cameraCenter)
	local margin = BuildGridConfig.cellSize * 2
	local limitX = math.max(0, BuildGridConfig.width * BuildGridConfig.cellSize * 0.5 - margin)
	local limitZ = math.max(0, BuildGridConfig.depth * BuildGridConfig.cellSize * 0.5 - margin)
	localCenter = Vector3.new(
		math.clamp(localCenter.X, -limitX, limitX),
		0,
		math.clamp(localCenter.Z, -limitZ, limitZ)
	)
	self._cameraCenter = self._surface.CFrame:PointToWorldSpace(localCenter)
	local offset = Vector3.new(self._zoom * 0.58, self._zoom, self._zoom * 0.72)
	camera.CFrame = CFrame.lookAt(self._cameraCenter + offset, self._cameraCenter)
end

function GridBuildController._render(self: Controller, deltaTime: number)
	self:_updateCamera(deltaTime)
	local visible = self:_canBuild()
	self._panel.Visible = self._replicationRoot:GetAttribute("Phase") == "PREPARATION"
	self._ghost.Parent = if visible and self._placementActive then workspace else nil
	self._pathPreview.Parent = if visible and self._placementActive then workspace else nil
	if visible and self._placementActive then
		self:_renderGhost()
	end
end

function GridBuildController.update(self: Controller)
	local owner = self._replicationRoot:GetAttribute("BuildOwnerUserId")
		== Players.LocalPlayer.UserId
	local preparation = self._replicationRoot:GetAttribute("Phase") == "PREPARATION"
	self._confirmButton.Active = owner and preparation
	self._moveButton.Visible = self._selectedPieceId ~= nil
	self._deleteButton.Visible = self._selectedPieceId ~= nil
	self._zoomOutButton.Visible = self._selectedPieceId == nil
	self._zoomInButton.Visible = self._selectedPieceId == nil
	if preparation and not owner then
		self._info.Text = "MODE OBSERVATION\nPlan synchronisé en direct"
	end
end

return GridBuildController
