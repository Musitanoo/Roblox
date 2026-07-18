--!strict

local ReplicatedStorage = game:GetService("ReplicatedStorage")

type Rotation = number
type PieceType = "Wall" | "SlowTrap" | "Turret"
type BuildReason = string
type BuildPieceData = {
	id: string,
	pieceType: PieceType,
	cellX: number,
	cellZ: number,
	rotation: Rotation,
}
type BuildPlan = { schemaVersion: number, revision: number, pieces: { [string]: BuildPieceData } }
type GridModule = {
	CellKey: (number, number) -> string,
	IsInsideGrid: (number, number) -> boolean,
	GetOccupiedCells: (BuildPieceData) -> { { x: number, z: number } },
}
type GridConfig = {
	structureLimit: number,
	powerLimit: number,
	forbiddenCells: { [string]: boolean },
}
type PieceTuning = {
	canRotate: boolean,
	structureCost: number,
	powerCost: number,
}

local sharedGame = ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Game")
local config = sharedGame:WaitForChild("Config")
local BuildGridConfig =
	require(config:WaitForChild("BuildGridConfig") :: ModuleScript) :: GridConfig
local PieceConfig = require(config:WaitForChild("PieceConfig") :: ModuleScript) :: {
	[string]: PieceTuning,
}
local GridMath = require(sharedGame:WaitForChild("GridMath") :: ModuleScript) :: GridModule

local BuildRules = {}

function BuildRules.CalculateBudgets(plan: BuildPlan): (number, number)
	local structure = 0
	local power = 0
	for _, piece in plan.pieces do
		local tuning = PieceConfig[piece.pieceType]
		if tuning then
			structure += tuning.structureCost
			power += tuning.powerCost
		end
	end
	return structure, power
end

function BuildRules.BuildOccupancy(plan: BuildPlan, ignorePieceId: string?): { [string]: string }
	local occupancy: { [string]: string } = {}
	for pieceId, piece in plan.pieces do
		if pieceId ~= ignorePieceId then
			for _, cell in GridMath.GetOccupiedCells(piece) do
				occupancy[GridMath.CellKey(cell.x, cell.z)] = pieceId
			end
		end
	end
	return occupancy
end

function BuildRules.ValidatePiece(
	plan: BuildPlan,
	piece: BuildPieceData,
	ignorePieceId: string?
): (boolean, BuildReason?)
	local tuning = PieceConfig[piece.pieceType]
	if not tuning then
		return false, "INVALID_PIECE"
	end
	if piece.rotation < 0 or piece.rotation > 3 or piece.rotation ~= math.floor(piece.rotation) then
		return false, "INVALID_ROTATION"
	end
	if not tuning.canRotate and piece.rotation ~= 0 then
		return false, "INVALID_ROTATION"
	end

	local occupancy = BuildRules.BuildOccupancy(plan, ignorePieceId)
	for _, cell in GridMath.GetOccupiedCells(piece) do
		if not GridMath.IsInsideGrid(cell.x, cell.z) then
			return false, "OUTSIDE_GRID"
		end
		local key = GridMath.CellKey(cell.x, cell.z)
		if BuildGridConfig.forbiddenCells[key] then
			return false, "FORBIDDEN_CELL"
		end
		if occupancy[key] then
			return false, "OCCUPIED"
		end
	end

	local structure, power = BuildRules.CalculateBudgets(plan)
	if not plan.pieces[piece.id] or piece.id == ignorePieceId then
		if ignorePieceId then
			local existing = plan.pieces[ignorePieceId]
			if existing then
				local oldTuning = PieceConfig[existing.pieceType]
				structure -= oldTuning.structureCost
				power -= oldTuning.powerCost
			end
		end
		structure += tuning.structureCost
		power += tuning.powerCost
	end
	if structure > BuildGridConfig.structureLimit then
		return false, "STRUCTURE_LIMIT"
	end
	if power > BuildGridConfig.powerLimit then
		return false, "POWER_LIMIT"
	end
	return true, nil
end

return table.freeze(BuildRules)
