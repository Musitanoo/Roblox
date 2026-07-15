--!strict

local CollectionService = game:GetService("CollectionService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

type PieceType = "Wall" | "SlowTrap" | "Turret"
type BuildPieceData = {
	id: string,
	pieceType: PieceType,
	cellX: number,
	cellZ: number,
	rotation: number,
}
type BuildPlan = { schemaVersion: number, revision: number, pieces: { [string]: BuildPieceData } }
type GridModule = {
	GetPieceWorldCFrame: (CFrame, BuildPieceData) -> CFrame,
	GetFootprint: (PieceType, number) -> (number, number),
}
type PieceTuning = { footprintWidth: number, footprintDepth: number, queryHeight: number }

local sharedGame = ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Game")
local config = sharedGame:WaitForChild("Config")
local GridMath = require(sharedGame:WaitForChild("GridMath") :: ModuleScript) :: GridModule
local PieceConfig =
	require(config:WaitForChild("PieceConfig") :: ModuleScript) :: { [string]: PieceTuning }

local BuildRenderer = {}
BuildRenderer.__index = BuildRenderer

export type Renderer = typeof(setmetatable(
	{} :: {
		_surface: BasePart,
		_templates: Folder,
		_runtime: Folder,
		_models: { [string]: Model },
	},
	BuildRenderer
))

local function findOrCreateFolder(parent: Instance, name: string): Folder
	local existing = parent:FindFirstChild(name)
	if existing then
		assert(existing:IsA("Folder"))
		return existing
	end
	local folder = Instance.new("Folder")
	folder.Name = name
	folder.Parent = parent
	return folder
end

function BuildRenderer.new(prototype: Folder, gameTemplates: Folder): Renderer
	local surface = prototype:FindFirstChild("BuildSurface")
	assert(surface ~= nil, "Prototype.BuildSurface is required")
	assert(surface:IsA("BasePart"), "Prototype.BuildSurface must be a BasePart")
	local templates = gameTemplates:FindFirstChild("BuildPieces")
	assert(templates ~= nil, "GameTemplates.BuildPieces is required")
	assert(templates:IsA("Folder"), "GameTemplates.BuildPieces must be a Folder")
	local runtime = findOrCreateFolder(findOrCreateFolder(prototype, "Runtime"), "Defenses")
	return setmetatable(
		{ _surface = surface, _templates = templates, _runtime = runtime, _models = {} },
		BuildRenderer
	)
end

function BuildRenderer.GetSurface(self: Renderer): BasePart
	return self._surface
end

function BuildRenderer.GetModel(self: Renderer, pieceId: string): Model?
	return self._models[pieceId]
end

function BuildRenderer.GetQueryBox(self: Renderer, piece: BuildPieceData): (CFrame, Vector3)
	local tuning = PieceConfig[piece.pieceType]
	local ground = GridMath.GetPieceWorldCFrame(self._surface.CFrame, piece)
	local height = tuning.queryHeight
	local boxCFrame = ground * CFrame.new(0, height * 0.5, 0)
	local boxSize =
		Vector3.new(tuning.footprintWidth * 4 - 0.3, height, tuning.footprintDepth * 4 - 0.3)
	return boxCFrame, boxSize
end

function BuildRenderer.Render(self: Renderer, plan: BuildPlan)
	for _, model in self._models do
		model:Destroy()
	end
	table.clear(self._models)
	for pieceId, piece in plan.pieces do
		local template = self._templates:FindFirstChild(piece.pieceType)
		assert(template ~= nil, "Missing build template " .. piece.pieceType)
		assert(template:IsA("Model"), "Build template must be a Model")
		assert(template.PrimaryPart ~= nil, "Build template requires PrimaryPart")
		local model = template:Clone()
		model.Name = pieceId .. "_" .. piece.pieceType
		model:SetAttribute("PieceId", pieceId)
		model:SetAttribute("PieceType", piece.pieceType)
		model:SetAttribute("DefenseType", piece.pieceType)
		model:SetAttribute("CellX", piece.cellX)
		model:SetAttribute("CellZ", piece.cellZ)
		model:SetAttribute("Rotation", piece.rotation)
		model:SetAttribute("OwnerUserId", 0)
		model:SetAttribute("PlanRevision", plan.revision)
		model:PivotTo(GridMath.GetPieceWorldCFrame(self._surface.CFrame, piece))
		model.Parent = self._runtime
		CollectionService:AddTag(model, "BuildPiece")
		self._models[pieceId] = model
	end
end

return BuildRenderer
