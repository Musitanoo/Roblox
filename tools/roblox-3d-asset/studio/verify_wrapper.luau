--!nonstrict
-- Operator snippet returns heterogeneous evidence records through Studio MCP.
-- Read-only wrapper verification.
local ASSET_KEY = "defense_barricade_small"
local EXPECTED_SIZE = Vector3.new(8, 4, 2)
local DIMENSION_TOLERANCE = 0.01
local runtime = workspace:FindFirstChild(ASSET_KEY .. "_Runtime")
if not runtime then
	return { status = "BLOCKED", mutationPerformed = false, errors = { "runtime wrapper missing" } }
end

local errors = {}
local evidence = { packageLinks = 0, visualBaseParts = 0, rollbackRoots = 0 }

local function requireChild(parent: Instance, name: string): Instance?
	local child = parent:FindFirstChild(name)
	if not child then
		table.insert(errors, "missing " .. name)
	end
	return child
end

local visual = requireChild(runtime, "Visual")
requireChild(runtime, "Visual_Staging")
local rollback = requireChild(runtime, "Visual_Rollback")
local collision = requireChild(runtime, "Collision")
requireChild(runtime, "Interaction")
requireChild(runtime, "Attachments")
requireChild(runtime, "Metadata")
requireChild(runtime, "RuntimeScripts")

if visual then
	local roots = visual:GetChildren()
	if #roots ~= 1 then
		table.insert(errors, "Visual must have exactly one active root")
	end
	for _, instance in visual:GetDescendants() do
		if instance:IsA("PackageLink") then
			evidence.packageLinks += 1
		elseif instance:IsA("BaseScript") then
			table.insert(errors, "visual contains script: " .. instance:GetFullName())
		elseif instance:IsA("BasePart") then
			evidence.visualBaseParts += 1
			if instance.CanCollide or instance.CanTouch then
				table.insert(
					errors,
					"visual BasePart has gameplay collision/touch enabled: "
						.. instance:GetFullName()
				)
			end
		end
	end
end

if rollback then
	evidence.rollbackRoots = #rollback:GetChildren()
end
if collision then
	local hitbox = requireChild(collision, "MainHitbox")
	requireChild(collision, "PlacementFootprint")
	if hitbox and hitbox:IsA("BasePart") then
		local errorVector = Vector3.new(
			math.abs(hitbox.Size.X - EXPECTED_SIZE.X) / EXPECTED_SIZE.X,
			math.abs(hitbox.Size.Y - EXPECTED_SIZE.Y) / EXPECTED_SIZE.Y,
			math.abs(hitbox.Size.Z - EXPECTED_SIZE.Z) / EXPECTED_SIZE.Z
		)
		if
			errorVector.X > DIMENSION_TOLERANCE
			or errorVector.Y > DIMENSION_TOLERANCE
			or errorVector.Z > DIMENSION_TOLERANCE
		then
			table.insert(errors, "MainHitbox dimensions exceed tolerance")
		end
	end
end

return {
	status = if #errors == 0 then "PASS" else "FAIL",
	mutationPerformed = false,
	errors = errors,
	evidence = evidence,
}
