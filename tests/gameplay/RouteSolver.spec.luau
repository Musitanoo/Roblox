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
type BuildPlan = {
	schemaVersion: number,
	revision: number,
	pieces: { [string]: BuildPieceData },
}
type Cell = { x: number, z: number }
type RouteSolverModule = {
	Solve: (BuildPlan, "Left" | "Right", "Roamer" | "Brute") -> ({ Cell }?, number),
}

local sharedGame = ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Game")
local RouteSolver =
	require(sharedGame:WaitForChild("RouteSolver") :: ModuleScript) :: RouteSolverModule

local RouteSolverSpec = {}

local function expect(condition: boolean, message: string)
	if not condition then
		error(message, 2)
	end
end

local function planWithGoalPiece(pieceType: PieceType): BuildPlan
	return {
		schemaVersion = 1,
		revision = 0,
		pieces = {
			goal = {
				id = "goal",
				pieceType = pieceType,
				cellX = 7,
				cellZ = 1,
				rotation = 0,
			},
		},
	}
end

function RouteSolverSpec.run()
	local empty: BuildPlan = {
		schemaVersion = 1,
		revision = 0,
		pieces = {},
	}
	local emptyPath, emptyCost = RouteSolver.Solve(empty, "Left", "Roamer")
	expect(emptyPath ~= nil and #emptyPath > 0, "empty live occupancy must yield a route")

	local turretPath, turretCost = RouteSolver.Solve(planWithGoalPiece("Turret"), "Left", "Roamer")
	expect(turretPath ~= nil, "a Turret cell must remain traversable")
	expect(turretCost == emptyCost, "Turrets must add no route-solver surcharge")

	local trapPath, trapCost = RouteSolver.Solve(planWithGoalPiece("SlowTrap"), "Left", "Roamer")
	expect(trapPath ~= nil, "a SlowTrap cell must remain traversable")
	expect(trapCost == emptyCost + 15, "an unavoidable SlowTrap cell must add exactly 15")

	local wallPath, wallCost = RouteSolver.Solve(planWithGoalPiece("Wall"), "Left", "Brute")
	expect(wallPath ~= nil, "a Wall cell must remain attackably traversable")
	expect(wallCost == emptyCost + 40, "an unavoidable Wall cell must add exactly 40")
end

return table.freeze(RouteSolverSpec)
