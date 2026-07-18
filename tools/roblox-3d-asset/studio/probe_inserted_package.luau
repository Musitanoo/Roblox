--!nonstrict
-- Operator snippet returns heterogeneous evidence records through Studio MCP.
-- Read-only probe. Rename STAGED_ROOT_NAME only after MCP inserted the staging Package.
local STAGED_ROOT_NAME = "R3D_StagedPackage"
local root = workspace:FindFirstChild(STAGED_ROOT_NAME)
if not root then
	return {
		status = "BLOCKED",
		mutationPerformed = false,
		reason = "staged Package root not found",
		expectedPath = "Workspace." .. STAGED_ROOT_NAME,
	}
end

local errors = {}
local evidence = {
	rootClass = root.ClassName,
	rootPath = root:GetFullName(),
	meshParts = 0,
	baseParts = 0,
	packageLinks = {},
	scripts = {},
}

for _, instance in root:GetDescendants() do
	if instance:IsA("MeshPart") then
		evidence.meshParts += 1
	end
	if instance:IsA("BasePart") then
		evidence.baseParts += 1
	end
	if instance:IsA("BaseScript") then
		table.insert(evidence.scripts, instance:GetFullName())
		table.insert(errors, "visual Package contains a script")
	end
	if instance:IsA("PackageLink") then
		local item = { path = instance:GetFullName() }
		local okPackageId, packageId = pcall(function()
			return instance.PackageId
		end)
		item.packageIdReadable = okPackageId
		item.packageId = if okPackageId then tostring(packageId) else nil
		local okVersion, versionNumber = pcall(function()
			return instance.VersionNumber
		end)
		item.versionNumberReadable = okVersion
		item.versionNumber = if okVersion then versionNumber else nil
		table.insert(evidence.packageLinks, item)
	end
end

if evidence.baseParts == 0 then
	table.insert(errors, "staged Package has no BasePart")
end

return {
	status = if #errors == 0 then "PASS" else "FAIL",
	mutationPerformed = false,
	errors = errors,
	evidence = evidence,
}
