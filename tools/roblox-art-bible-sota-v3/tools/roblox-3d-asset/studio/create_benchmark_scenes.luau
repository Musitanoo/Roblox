--!nonstrict
-- Operator snippet returns heterogeneous evidence records through Studio MCP.
-- Creates disabled benchmark fixtures in ServerStorage. Keep DRY_RUN=true for the first pass.
local DRY_RUN = true
local ASSET_KEY = "defense_barricade_small"
local COUNTS = { 0, 1, 30, 100 }
local runtime = workspace:FindFirstChild(ASSET_KEY .. "_Runtime")
if not runtime or not runtime:IsA("Model") then
	return { status = "BLOCKED", mutationPerformed = false, reason = "runtime wrapper missing" }
end

local plan =
	{ storage = "ServerStorage.R3D_BenchmarkScenes", counts = COUNTS, activeWorkspaceCopies = 0 }
if DRY_RUN then
	return { status = "PARTIAL", mutationPerformed = false, dryRun = true, plan = plan }
end

local ServerStorage = game:GetService("ServerStorage")
if ServerStorage:FindFirstChild("R3D_BenchmarkScenes") then
	return {
		status = "BLOCKED",
		mutationPerformed = false,
		reason = "benchmark fixtures already exist",
	}
end

local root = Instance.new("Folder")
root.Name = "R3D_BenchmarkScenes"
root.Parent = ServerStorage
for _, count in COUNTS do
	local scene = Instance.new("Folder")
	scene.Name = "Scene_" .. tostring(count)
	scene:SetAttribute("InstanceCount", count)
	scene.Parent = root
	for index = 1, count do
		local clone = runtime:Clone()
		clone.Name = ASSET_KEY .. "_" .. tostring(index)
		local row = math.floor((index - 1) / 10)
		local column = (index - 1) % 10
		clone:PivotTo(CFrame.new(column * 12, 0, row * 8))
		clone.Parent = scene
	end
end

return { status = "PASS", mutationPerformed = true, root = root:GetFullName(), plan = plan }
