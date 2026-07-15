--!strict

local ReplicatedStorage = game:GetService("ReplicatedStorage")

type PieceType = "Wall" | "SlowTrap" | "Turret"
type BuildPieceData = {
	id: string,
	pieceType: PieceType,
	cellX: number,
	cellZ: number,
	rotation: number,
}
export type BuildPlan = {
	schemaVersion: number,
	revision: number,
	pieces: { [string]: BuildPieceData },
}
type GridConfig = { schemaVersion: number }

local sharedGame = ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Game")
local config = sharedGame:WaitForChild("Config")
local BuildGridConfig =
	require(config:WaitForChild("BuildGridConfig") :: ModuleScript) :: GridConfig

local BuildPlanStore = {}
BuildPlanStore.__index = BuildPlanStore

export type Store = typeof(setmetatable(
	{} :: {
		_plan: BuildPlan,
		_nextPieceNumber: number,
	},
	BuildPlanStore
))

local function clonePiece(piece: BuildPieceData): BuildPieceData
	return {
		id = piece.id,
		pieceType = piece.pieceType,
		cellX = piece.cellX,
		cellZ = piece.cellZ,
		rotation = piece.rotation,
	}
end

local function clonePlan(plan: BuildPlan): BuildPlan
	local pieces: { [string]: BuildPieceData } = {}
	for id, piece in plan.pieces do
		pieces[id] = clonePiece(piece)
	end
	return { schemaVersion = plan.schemaVersion, revision = plan.revision, pieces = pieces }
end

function BuildPlanStore.new(): Store
	return setmetatable({
		_plan = { schemaVersion = BuildGridConfig.schemaVersion, revision = 0, pieces = {} },
		_nextPieceNumber = 1,
	}, BuildPlanStore)
end

function BuildPlanStore.ClonePlan(_self: Store, plan: BuildPlan): BuildPlan
	return clonePlan(plan)
end
function BuildPlanStore.GetPlan(self: Store): BuildPlan
	return clonePlan(self._plan)
end

function BuildPlanStore.NewPieceId(self: Store): string
	local id = string.format("P%05d", self._nextPieceNumber)
	self._nextPieceNumber += 1
	return id
end

function BuildPlanStore.CommitPieces(self: Store, pieces: { [string]: BuildPieceData }): BuildPlan
	local nextPlan: BuildPlan = {
		schemaVersion = BuildGridConfig.schemaVersion,
		revision = self._plan.revision + 1,
		pieces = {},
	}
	for id, piece in pieces do
		nextPlan.pieces[id] = clonePiece(piece)
	end
	self._plan = nextPlan
	return self:GetPlan()
end

function BuildPlanStore.Replace(self: Store, plan: BuildPlan, preserveRevision: boolean): BuildPlan
	local nextPlan = clonePlan(plan)
	nextPlan.schemaVersion = BuildGridConfig.schemaVersion
	if not preserveRevision then
		nextPlan.revision = self._plan.revision + 1
	end
	self._plan = nextPlan
	return self:GetPlan()
end

return BuildPlanStore
