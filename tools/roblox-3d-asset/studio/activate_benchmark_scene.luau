--!nonstrict
-- Operator snippet returns heterogeneous evidence records through Studio MCP.
-- Activates exactly one prepared fixture. Keep DRY_RUN=true for the first pass.
local DRY_RUN = true
local TARGET_COUNT = 30
local VALID_COUNTS = { [0] = true, [1] = true, [30] = true, [100] = true }
if not VALID_COUNTS[TARGET_COUNT] then
	return {
		status = "FAIL",
		mutationPerformed = false,
		reason = "TARGET_COUNT must be 0, 1, 30, or 100",
	}
end

local ServerStorage = game:GetService("ServerStorage")
local fixtures = ServerStorage:FindFirstChild("R3D_BenchmarkScenes")
local source = fixtures and fixtures:FindFirstChild("Scene_" .. tostring(TARGET_COUNT))
if not source then
	return {
		status = "BLOCKED",
		mutationPerformed = false,
		reason = "requested benchmark fixture missing",
	}
end

local existing = workspace:FindFirstChild("R3D_ActiveBenchmark")
local plan = { targetCount = TARGET_COUNT, replacesExistingActiveScene = existing ~= nil }
if DRY_RUN then
	return { status = "PARTIAL", mutationPerformed = false, dryRun = true, plan = plan }
end
if existing then
	existing:Destroy()
end
local active = source:Clone()
active.Name = "R3D_ActiveBenchmark"
active.Parent = workspace
return {
	status = "PASS",
	mutationPerformed = true,
	active = active:GetFullName(),
	count = TARGET_COUNT,
}
