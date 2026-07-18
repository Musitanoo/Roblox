--!strict

export type Rotation = number
export type PieceType = "Wall" | "SlowTrap" | "Turret"
export type BuildOperation = "PLACE" | "MOVE" | "ROTATE" | "DELETE" | "UNDO" | "REDO" | "CLEAR_ALL"
export type BuildReason =
	"OUTSIDE_GRID"
	| "FORBIDDEN_CELL"
	| "OCCUPIED"
	| "WORLD_OVERLAP"
	| "STRUCTURE_LIMIT"
	| "POWER_LIMIT"
	| "INVALID_PIECE"
	| "INVALID_ROTATION"
	| "NOT_OWNER"
	| "WRONG_STATE"
	| "STALE_REVISION"
	| "RATE_LIMITED"
	| "REQUEST_CONFLICT"

export type BuildPieceData = {
	id: string,
	pieceType: PieceType,
	cellX: number,
	cellZ: number,
	rotation: Rotation,
}

export type BuildPlan = {
	schemaVersion: number,
	revision: number,
	pieces: { [string]: BuildPieceData },
}

export type BuildRequest = {
	requestId: string,
	baseRevision: number,
	operation: BuildOperation,
	payload: { [string]: unknown },
}

export type BuildResult = {
	requestId: string,
	success: boolean,
	reason: BuildReason?,
	revision: number,
	delta: { [string]: unknown }?,
	structureUsed: number,
	powerUsed: number,
}

local PIECE_TYPES: { [string]: boolean } = { Wall = true, SlowTrap = true, Turret = true }

local BuildTypes = {}

function BuildTypes.isPieceType(value: unknown): boolean
	return typeof(value) == "string" and PIECE_TYPES[value] == true
end

function BuildTypes.isRotation(value: unknown): boolean
	return typeof(value) == "number" and value == math.floor(value) and value >= 0 and value <= 3
end

return table.freeze(BuildTypes)
