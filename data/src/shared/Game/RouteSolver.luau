--!strict

local ReplicatedStorage = game:GetService("ReplicatedStorage")

type RouteId = "Left" | "Right"
type EnemyType = "Roamer" | "Brute"
type PieceType = "Wall" | "SlowTrap" | "Turret"
type BuildPieceData = {
	id: string,
	pieceType: PieceType,
	cellX: number,
	cellZ: number,
	rotation: number,
}
type BuildPlan = { schemaVersion: number, revision: number, pieces: { [string]: BuildPieceData } }
type Cell = { x: number, z: number }
type GridModule = {
	CellKey: (number, number) -> string,
	IsInsideGrid: (number, number) -> boolean,
	GetOccupiedCells: (BuildPieceData) -> { Cell },
}
type GridConfig = {
	forbiddenCells: { [string]: boolean },
	startCells: { [string]: Cell },
	goalCells: { [string]: Cell },
}
type PieceTuning = { roamerCost: number, bruteCost: number }

local sharedGame = ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Game")
local config = sharedGame:WaitForChild("Config")
local BuildGridConfig =
	require(config:WaitForChild("BuildGridConfig") :: ModuleScript) :: GridConfig
local PieceConfig = require(config:WaitForChild("PieceConfig") :: ModuleScript) :: {
	[string]: PieceTuning,
}
local GridMath = require(sharedGame:WaitForChild("GridMath") :: ModuleScript) :: GridModule

local RouteSolver = {}

local function heuristic(a: Cell, b: Cell): number
	return math.abs(a.x - b.x) + math.abs(a.z - b.z)
end

local function occupancyFor(plan: BuildPlan): { [string]: PieceType }
	local result: { [string]: PieceType } = {}
	for _, piece in plan.pieces do
		for _, cell in GridMath.GetOccupiedCells(piece) do
			result[GridMath.CellKey(cell.x, cell.z)] = piece.pieceType
		end
	end
	return result
end

local function stepCost(
	occupancy: { [string]: PieceType },
	cell: Cell,
	enemyType: EnemyType
): number
	local pieceType = occupancy[GridMath.CellKey(cell.x, cell.z)]
	if not pieceType then
		return 10
	end
	local tuning = PieceConfig[pieceType]
	return if enemyType == "Brute" then tuning.bruteCost else tuning.roamerCost
end

function RouteSolver.Solve(
	plan: BuildPlan,
	routeId: RouteId,
	enemyType: EnemyType
): ({ Cell }?, number)
	local start = BuildGridConfig.startCells[routeId]
	local goal = BuildGridConfig.goalCells[routeId]
	if not start or not goal then
		return nil, math.huge
	end
	local occupancy = occupancyFor(plan)
	local startKey = GridMath.CellKey(start.x, start.z)
	local open: { Cell } = { { x = start.x, z = start.z } }
	local openSet: { [string]: boolean } = { [startKey] = true }
	local cameFrom: { [string]: string } = {}
	local cells: { [string]: Cell } = { [startKey] = { x = start.x, z = start.z } }
	local gScore: { [string]: number } = { [startKey] = 0 }
	local fScore: { [string]: number } = { [startKey] = heuristic(start, goal) * 10 }

	while #open > 0 do
		local bestIndex = 1
		for index = 2, #open do
			local candidate = open[index]
			local best = open[bestIndex]
			local candidateKey = GridMath.CellKey(candidate.x, candidate.z)
			local bestKey = GridMath.CellKey(best.x, best.z)
			local candidateF = fScore[candidateKey] or math.huge
			local bestF = fScore[bestKey] or math.huge
			if
				candidateF < bestF
				or (
					candidateF == bestF
					and (candidate.z < best.z or (candidate.z == best.z and candidate.x < best.x))
				)
			then
				bestIndex = index
			end
		end

		local current = table.remove(open, bestIndex)
		assert(current ~= nil, "Open route set cannot be empty inside the solver loop")
		local currentKey = GridMath.CellKey(current.x, current.z)
		openSet[currentKey] = nil
		if current.x == goal.x and current.z == goal.z then
			local path: { Cell } = { current }
			while cameFrom[currentKey] do
				currentKey = cameFrom[currentKey]
				table.insert(path, 1, cells[currentKey])
			end
			return path, gScore[GridMath.CellKey(goal.x, goal.z)] or 0
		end

		for _, offset in ipairs({ { 0, -1 }, { -1, 0 }, { 1, 0 }, { 0, 1 } }) do
			local neighbor: Cell = { x = current.x + offset[1], z = current.z + offset[2] }
			local neighborKey = GridMath.CellKey(neighbor.x, neighbor.z)
			if
				GridMath.IsInsideGrid(neighbor.x, neighbor.z)
				and not BuildGridConfig.forbiddenCells[neighborKey]
			then
				local tentative = (gScore[currentKey] or math.huge)
					+ stepCost(occupancy, neighbor, enemyType)
				if tentative < (gScore[neighborKey] or math.huge) then
					cameFrom[neighborKey] = currentKey
					cells[neighborKey] = neighbor
					gScore[neighborKey] = tentative
					fScore[neighborKey] = tentative + heuristic(neighbor, goal) * 10
					if not openSet[neighborKey] then
						table.insert(open, neighbor)
						openSet[neighborKey] = true
					end
				end
			end
		end
	end
	return nil, math.huge
end

return table.freeze(RouteSolver)
