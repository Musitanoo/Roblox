--!nonstrict
-- Operator snippet returns heterogeneous evidence records through Studio MCP.
-- Operator script. Execute once in Edit mode. Keep DRY_RUN=true for the first pass.
local DRY_RUN = true
local ASSET_KEY = "defense_barricade_small"
local STAGED_ROOT_NAME = "R3D_StagedPackage"
local EXPECTED_SIZE = Vector3.new(8, 4, 2)
local DIMENSION_TOLERANCE = 0.01

local stagedRoot = workspace:FindFirstChild(STAGED_ROOT_NAME)
if not stagedRoot then
	return { status = "BLOCKED", mutationPerformed = false, reason = "staged Package root missing" }
end

local runtimeName = ASSET_KEY .. "_Runtime"
if workspace:FindFirstChild(runtimeName) then
	return { status = "FAIL", mutationPerformed = false, reason = runtimeName .. " already exists" }
end

for _, instance in stagedRoot:GetDescendants() do
	if instance:IsA("BaseScript") then
		return {
			status = "FAIL",
			mutationPerformed = false,
			reason = "visual Package contains script: " .. instance:GetFullName(),
		}
	end
end

local function getBounds(root: Instance): (CFrame, Vector3)
	if root:IsA("Model") then
		return root:GetBoundingBox()
	end
	if root:IsA("BasePart") then
		return root.CFrame, root.Size
	end
	error("staged root must be a Model or BasePart")
end

local boundsCFrame, boundsSize = getBounds(stagedRoot)
local sizeError = Vector3.new(
	math.abs(boundsSize.X - EXPECTED_SIZE.X) / EXPECTED_SIZE.X,
	math.abs(boundsSize.Y - EXPECTED_SIZE.Y) / EXPECTED_SIZE.Y,
	math.abs(boundsSize.Z - EXPECTED_SIZE.Z) / EXPECTED_SIZE.Z
)
if
	sizeError.X > DIMENSION_TOLERANCE
	or sizeError.Y > DIMENSION_TOLERANCE
	or sizeError.Z > DIMENSION_TOLERANCE
then
	return {
		status = "FAIL",
		mutationPerformed = false,
		reason = "staged Package dimensions exceed tolerance",
		observedSize = tostring(boundsSize),
		relativeError = tostring(sizeError),
	}
end

local plan = {
	runtimeName = runtimeName,
	visualRoot = stagedRoot:GetFullName(),
	visualSize = tostring(boundsSize),
	collision = "two explicit invisible Parts",
}
if DRY_RUN then
	return { status = "PARTIAL", mutationPerformed = false, dryRun = true, plan = plan }
end

local runtime = Instance.new("Model")
runtime.Name = runtimeName
runtime:SetAttribute("AssetKey", ASSET_KEY)
runtime:SetAttribute("WrapperSchemaVersion", "1.0.0")

local visual = Instance.new("Folder")
visual.Name = "Visual"
visual.Parent = runtime
local staging = Instance.new("Folder")
staging.Name = "Visual_Staging"
staging.Parent = runtime
local rollback = Instance.new("Folder")
rollback.Name = "Visual_Rollback"
rollback.Parent = runtime
local collision = Instance.new("Folder")
collision.Name = "Collision"
collision.Parent = runtime
local interaction = Instance.new("Folder")
interaction.Name = "Interaction"
interaction.Parent = runtime
local attachments = Instance.new("Folder")
attachments.Name = "Attachments"
attachments.Parent = runtime
local metadata = Instance.new("Folder")
metadata.Name = "Metadata"
metadata.Parent = runtime
local runtimeScripts = Instance.new("Folder")
runtimeScripts.Name = "RuntimeScripts"
runtimeScripts.Parent = runtime

stagedRoot.Parent = visual
for _, instance in stagedRoot:GetDescendants() do
	if instance:IsA("BasePart") then
		instance.Anchored = true
		instance.CanCollide = false
		instance.CanTouch = false
		instance.CanQuery = true
		instance.CastShadow = true
		if instance:IsA("MeshPart") then
			instance.RenderFidelity = Enum.RenderFidelity.Automatic
		end
	end
end

local mainHitbox = Instance.new("Part")
mainHitbox.Name = "MainHitbox"
mainHitbox.Size = EXPECTED_SIZE
mainHitbox.CFrame = boundsCFrame
mainHitbox.Transparency = 1
mainHitbox.Anchored = true
mainHitbox.CanCollide = true
mainHitbox.CanQuery = true
mainHitbox.CanTouch = false
mainHitbox.Parent = collision

local footprint = Instance.new("Part")
footprint.Name = "PlacementFootprint"
footprint.Size = Vector3.new(EXPECTED_SIZE.X, 0.2, EXPECTED_SIZE.Z)
footprint.CFrame = boundsCFrame * CFrame.new(0, -EXPECTED_SIZE.Y / 2 + 0.1, 0)
footprint.Transparency = 1
footprint.Anchored = true
footprint.CanCollide = false
footprint.CanQuery = true
footprint.CanTouch = false
footprint.Parent = collision

runtime.Parent = workspace
return {
	status = "PASS",
	mutationPerformed = true,
	runtimePath = runtime:GetFullName(),
	plan = plan,
}
