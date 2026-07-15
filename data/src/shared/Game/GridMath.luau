--!strict

local ReplicatedStorage = game:GetService("ReplicatedStorage")

type Rotation = number
type PieceType = "Wall" | "SlowTrap" | "Turret"
type BuildPieceData = {
	id: string,
	pieceType: PieceType,
	cellX: number,
	cellZ: number,
	rotation: Rotation,
}
type Cell = { x: number, z: number }
type GridConfig = { width: number, depth: number, cellSize: number }
type PieceTuning = { footprintWidth: number, footprintDepth: number }

local sharedGame = ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Game")
local config = sharedGame:WaitForChild("Config")
local BuildGridConfig =
	require(config:WaitForChild("BuildGridConfig") :: ModuleScript) :: GridConfig
local PieceConfig = require(config:WaitForChild("PieceConfig") :: ModuleScript) :: {
	[string]: PieceTuning,
}

local GridMath = {}

function GridMath.CellKey(cellX: number, cellZ: number): string
	return string.format("%d:%d", cellX, cellZ)
end

function GridMath.IsInsideGrid(cellX: number, cellZ: number): boolean
	return cellX >= 1
		and cellX <= BuildGridConfig.width
		and cellZ >= 1
		and cellZ <= BuildGridConfig.depth
end

function GridMath.WorldToCell(buildSurfaceCFrame: CFrame, worldPosition: Vector3): (number, number)
	local localPosition = buildSurfaceCFrame:PointToObjectSpace(worldPosition)
	local halfWidth = BuildGridConfig.width * BuildGridConfig.cellSize * 0.5
	local halfDepth = BuildGridConfig.depth * BuildGridConfig.cellSize * 0.5
	local cellX = math.floor((localPosition.X + halfWidth) / BuildGridConfig.cellSize) + 1
	local cellZ = math.floor((localPosition.Z + halfDepth) / BuildGridConfig.cellSize) + 1
	return cellX, cellZ
end

function GridMath.CellToWorld(buildSurfaceCFrame: CFrame, cellX: number, cellZ: number): Vector3
	local halfWidth = BuildGridConfig.width * BuildGridConfig.cellSize * 0.5
	local halfDepth = BuildGridConfig.depth * BuildGridConfig.cellSize * 0.5
	local localX = (cellX - 0.5) * BuildGridConfig.cellSize - halfWidth
	local localZ = (cellZ - 0.5) * BuildGridConfig.cellSize - halfDepth
	return buildSurfaceCFrame:PointToWorldSpace(Vector3.new(localX, 0, localZ))
end

function GridMath.GetFootprint(pieceType: PieceType, rotation: Rotation): (number, number)
	local tuning = PieceConfig[pieceType]
	if rotation % 2 == 1 then
		return tuning.footprintDepth, tuning.footprintWidth
	end
	return tuning.footprintWidth, tuning.footprintDepth
end

function GridMath.GetOccupiedCells(pieceData: BuildPieceData): { Cell }
	local width, depth = GridMath.GetFootprint(pieceData.pieceType, pieceData.rotation)
	local result: { Cell } = {}
	for offsetZ = 0, depth - 1 do
		for offsetX = 0, width - 1 do
			table.insert(result, { x = pieceData.cellX + offsetX, z = pieceData.cellZ + offsetZ })
		end
	end
	return result
end

function GridMath.GetPieceWorldCFrame(buildSurfaceCFrame: CFrame, pieceData: BuildPieceData): CFrame
	local width, depth = GridMath.GetFootprint(pieceData.pieceType, pieceData.rotation)
	local first = GridMath.CellToWorld(buildSurfaceCFrame, pieceData.cellX, pieceData.cellZ)
	local last = GridMath.CellToWorld(
		buildSurfaceCFrame,
		pieceData.cellX + width - 1,
		pieceData.cellZ + depth - 1
	)
	local center = (first + last) * 0.5
	return CFrame.new(center)
		* buildSurfaceCFrame.Rotation
		* CFrame.Angles(0, math.rad(pieceData.rotation * 90), 0)
end

return table.freeze(GridMath)
