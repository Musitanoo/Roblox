--!strict

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Workspace = game:GetService("Workspace")

type PieceType = "Wall" | "SlowTrap" | "Turret"
type BuildPieceData = {
	id: string,
	pieceType: PieceType,
	cellX: number,
	cellZ: number,
	rotation: number,
}
type BuildPlan = { schemaVersion: number, revision: number, pieces: { [string]: BuildPieceData } }
type BuildRulesModule =
	{ ValidatePiece: (BuildPlan, BuildPieceData, string?) -> (boolean, string?) }
type Renderer = {
	GetSurface: (self: Renderer) -> BasePart,
	GetQueryBox: (self: Renderer, BuildPieceData) -> (CFrame, Vector3),
}

local sharedGame = ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Game")
local BuildRules =
	require(sharedGame:WaitForChild("BuildRules") :: ModuleScript) :: BuildRulesModule

local BuildValidator = {}
BuildValidator.__index = BuildValidator
export type Validator = typeof(setmetatable(
	{} :: { _prototype: Folder, _renderer: Renderer },
	BuildValidator
))

function BuildValidator.new(prototype: Folder, renderer: Renderer): Validator
	return setmetatable({ _prototype = prototype, _renderer = renderer }, BuildValidator)
end

function BuildValidator.HasWorldOverlap(self: Validator, piece: BuildPieceData): boolean
	local queryCFrame, querySize = self._renderer:GetQueryBox(piece)
	local excluded: { Instance } = { self._renderer:GetSurface() }
	for _, name in ipairs({
		"BaseFloor",
		"Lanes",
		"ReviewMarkers",
		"EnemySpawns",
		"Runtime",
		"PlayerSpawn",
	}) do
		local instance = self._prototype:FindFirstChild(name)
		if instance then
			table.insert(excluded, instance)
		end
	end
	for _, player in Players:GetPlayers() do
		if player.Character then
			table.insert(excluded, player.Character)
		end
	end
	local params = OverlapParams.new()
	params.FilterType = Enum.RaycastFilterType.Exclude
	params.FilterDescendantsInstances = excluded
	params.MaxParts = 1
	return #Workspace:GetPartBoundsInBox(queryCFrame, querySize, params) > 0
end

function BuildValidator.Validate(
	self: Validator,
	plan: BuildPlan,
	piece: BuildPieceData,
	ignorePieceId: string?
): (boolean, string?)
	local valid, reason = BuildRules.ValidatePiece(plan, piece, ignorePieceId)
	if not valid then
		return false, reason
	end
	if self:HasWorldOverlap(piece) then
		return false, "WORLD_OVERLAP"
	end
	return true, nil
end

return BuildValidator
