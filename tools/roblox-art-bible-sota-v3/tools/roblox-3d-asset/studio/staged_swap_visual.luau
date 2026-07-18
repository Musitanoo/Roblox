--!nonstrict
-- Operator snippet returns heterogeneous evidence records through Studio MCP.
-- Recoverable staged replacement. This is intentionally not called atomic.
-- Keep DRY_RUN=true until the staged Package probe and wrapper verification pass.
local DRY_RUN = true
local ASSET_KEY = "defense_barricade_small"
local STAGED_ROOT_NAME = "R3D_StagedPackage"

local runtime = workspace:FindFirstChild(ASSET_KEY .. "_Runtime")
local stagedRoot = workspace:FindFirstChild(STAGED_ROOT_NAME)
if not runtime then
	return { status = "BLOCKED", mutationPerformed = false, reason = "runtime wrapper missing" }
end
if not stagedRoot then
	return { status = "BLOCKED", mutationPerformed = false, reason = "staged Package root missing" }
end

local visual = runtime:FindFirstChild("Visual")
local staging = runtime:FindFirstChild("Visual_Staging")
local rollback = runtime:FindFirstChild("Visual_Rollback")
if not visual or not staging or not rollback then
	return { status = "FAIL", mutationPerformed = false, reason = "wrapper visual folders missing" }
end
if #visual:GetChildren() ~= 1 then
	return {
		status = "FAIL",
		mutationPerformed = false,
		reason = "Visual must contain exactly one active root",
	}
end
if #staging:GetChildren() ~= 0 or #rollback:GetChildren() ~= 0 then
	return {
		status = "BLOCKED",
		mutationPerformed = false,
		reason = "staging and rollback folders must be empty",
	}
end

for _, instance in stagedRoot:GetDescendants() do
	if instance:IsA("BaseScript") then
		return {
			status = "FAIL",
			mutationPerformed = false,
			reason = "staged visual contains script: " .. instance:GetFullName(),
		}
	end
end

local oldRoot = visual:GetChildren()[1]
local plan = {
	operation = "REINSERT_STAGED_SWAP",
	oldRoot = oldRoot:GetFullName(),
	newRoot = stagedRoot:GetFullName(),
	rollbackRetained = true,
}
if DRY_RUN then
	return { status = "PARTIAL", mutationPerformed = false, dryRun = true, plan = plan }
end

stagedRoot.Parent = staging
oldRoot.Parent = rollback
stagedRoot.Parent = visual

if #visual:GetChildren() ~= 1 or visual:GetChildren()[1] ~= stagedRoot then
	stagedRoot.Parent = staging
	oldRoot.Parent = visual
	return {
		status = "FAIL",
		mutationPerformed = true,
		rollbackRestored = true,
		reason = "activation postcondition failed",
	}
end

return {
	status = "PASS",
	mutationPerformed = true,
	operation = "REINSERT_STAGED_SWAP",
	activeVisual = stagedRoot:GetFullName(),
	rollbackVisual = oldRoot:GetFullName(),
	cleanupRequiredAfterVerification = true,
}
