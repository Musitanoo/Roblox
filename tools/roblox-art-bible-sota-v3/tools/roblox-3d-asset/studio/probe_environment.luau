--!nonstrict
-- Operator snippet returns heterogeneous evidence records through Studio MCP.
-- Read-only capability probe. Safe to execute in Edit mode through Studio MCP.
local packageLinks = 0
local meshParts = 0
local visualScripts = 0

for _, instance in game:GetDescendants() do
	if instance:IsA("PackageLink") then
		packageLinks += 1
	elseif instance:IsA("MeshPart") then
		meshParts += 1
	elseif instance:IsA("BaseScript") then
		visualScripts += 1
	end
end

return {
	status = "PASS",
	mutationPerformed = false,
	place = {
		name = game.Name,
		placeId = game.PlaceId,
		gameId = game.GameId,
		creatorId = game.CreatorId,
		creatorType = tostring(game.CreatorType),
	},
	observed = {
		packageLinks = packageLinks,
		meshParts = meshParts,
		scriptsInDataModel = visualScripts,
		runtimeExists = workspace:FindFirstChild("defense_barricade_small_Runtime") ~= nil,
		stagedPackageExists = workspace:FindFirstChild("R3D_StagedPackage") ~= nil,
	},
}
