--!strict

local ServerStorage = game:GetService("ServerStorage")

local AssetKitStager = {}
local TERRITORIES = {
	["industrial-toy-defense"] = true,
	["salvaged-frontier"] = true,
	["clean-tactical-diorama"] = true,
}
local ASSETS = {
	barricade = true,
	objective_core = true,
	enemy_standard = true,
	floor_module = true,
	damage_effect = true,
}
local STATES = { intact = true, damaged = true, critical = true }
local APPLICABLE_STATES = {
	barricade = { intact = true, damaged = true, critical = true },
	objective_core = { intact = true, damaged = true, critical = true },
	enemy_standard = { intact = true, damaged = true, critical = true },
	floor_module = { intact = true, damaged = true },
	damage_effect = { damaged = true, critical = true },
}
local STUDIO_MATERIALS = {
	SmoothPlastic = Enum.Material.SmoothPlastic,
	Neon = Enum.Material.Neon,
	Rubber = Enum.Material.Rubber,
	Metal = Enum.Material.Metal,
	WoodPlanks = Enum.Material.WoodPlanks,
	Concrete = Enum.Material.Concrete,
	CorrodedMetal = Enum.Material.CorrodedMetal,
}

local function isSha256(value: any): boolean
	return type(value) == "string" and #value == 64 and string.match(value, "^[0-9a-f]+$") ~= nil
end

local function ensureFolder(parent: Instance, name: string): Folder
	local existing = parent:FindFirstChild(name)
	if existing and not existing:IsA("Folder") then
		error(`{parent:GetFullName()}.{name} exists but is not a Folder`)
	end
	if existing then
		return existing :: Folder
	end
	local folder = Instance.new("Folder")
	folder.Name = name
	folder.Parent = parent
	return folder
end

local function colorFromHex(hex: string): Color3
	local value = string.gsub(hex, "#", "")
	return Color3.fromRGB(
		tonumber(string.sub(value, 1, 2), 16) or 0,
		tonumber(string.sub(value, 3, 4), 16) or 0,
		tonumber(string.sub(value, 5, 6), 16) or 0
	)
end

local function roleForMesh(mesh: MeshPart, root: Instance): string?
	local cursor: Instance? = mesh
	while cursor do
		local role = string.match(cursor.Name, "^ROLE_([%w]+)$")
		if role then
			return role
		end
		if cursor == root then
			break
		end
		cursor = cursor.Parent
	end
	return nil
end

local function styleClone(clone: Instance, territory: string, territoryStyles: any): any
	local territoryStyle = territoryStyles.territories[territory]
	if not territoryStyle then
		return { ok = false, meshCount = 0, issues = { `Missing territory style: {territory}` } }
	end
	local candidates = { clone }
	for _, descendant in clone:GetDescendants() do
		table.insert(candidates, descendant)
	end
	local issues = {}
	local meshCount = 0
	for _, candidate in candidates do
		if not candidate:IsA("MeshPart") then
			continue
		end
		meshCount += 1
		local role = roleForMesh(candidate, clone)
		local profile = role and territoryStyles.roleProfiles[role]
		local colorHex = role and territoryStyle.palette[role]
		local surfaceId = role and territoryStyle.surfaceAssignments[role]
		local surface = surfaceId and territoryStyles.surfaceProfiles[surfaceId]
		if not role or not profile or not surface or type(colorHex) ~= "string" then
			table.insert(
				issues,
				`{candidate:GetFullName()}: missing or invalid ROLE_<semanticRole> identity`
			)
			continue
		end
		local material = STUDIO_MATERIALS[surface.studioMaterial]
		if not material then
			table.insert(
				issues,
				`{candidate:GetFullName()}: unsupported Studio material {surface.studioMaterial}`
			)
			continue
		end
		candidate.Color = colorFromHex(colorHex)
		candidate.Material = material
		candidate.CastShadow = profile.studio.castShadow
		candidate.RenderFidelity = Enum.RenderFidelity.Automatic
		candidate.Anchored = true
		candidate.CanCollide = false
		candidate.CanTouch = false
		candidate.CanQuery = false
		candidate.AudioCanCollide = false
		candidate.EnableFluidForces = false
		candidate.DoubleSided = false
		candidate:SetAttribute("ArtMaterialRole", role)
		candidate:SetAttribute("ArtSurfaceProfile", surfaceId)
	end
	if meshCount == 0 then
		table.insert(issues, "Imported asset contains no MeshPart")
	end
	return { ok = #issues == 0, meshCount = meshCount, issues = issues }
end

local function createHitbox(clone: Instance, assetId: string): number
	if assetId == "damage_effect" then
		return 0
	end
	local existing = clone:FindFirstChild("CollisionHitbox")
	if existing then
		existing:Destroy()
	end
	local cframe: CFrame
	local size: Vector3
	if clone:IsA("Model") then
		cframe, size = clone:GetBoundingBox()
	elseif clone:IsA("BasePart") then
		cframe, size = clone.CFrame, clone.Size
	else
		error(`Unsupported staged asset type {clone.ClassName}`)
	end
	local hitbox = Instance.new("Part")
	hitbox.Name = "CollisionHitbox"
	hitbox.Size = size
	hitbox.CFrame = cframe
	hitbox.Anchored = true
	hitbox.Transparency = 1
	hitbox.CastShadow = false
	hitbox.CanCollide = true
	hitbox.CanTouch = false
	hitbox.CanQuery = true
	hitbox.AudioCanCollide = false
	hitbox.EnableFluidForces = false
	hitbox:SetAttribute("ArtHitbox", true)
	hitbox.Parent = clone
	return 1
end

function AssetKitStager.stage(instances: { Instance }, territoryStyles: any): any
	local root = ensureFolder(ServerStorage, "ArtDirectionAssetKit")
	local issues = {}
	local staged = {}
	local styledMeshCount = 0
	local hitboxCount = 0
	for _, instance in instances do
		local territory = instance:GetAttribute("ArtTerritory")
		local assetId = instance:GetAttribute("ArtAssetId")
		local stateId = instance:GetAttribute("ArtState")
		if type(territory) ~= "string" or not TERRITORIES[territory] then
			table.insert(issues, `{instance:GetFullName()}: invalid ArtTerritory`)
			continue
		end
		if type(assetId) ~= "string" or not ASSETS[assetId] then
			table.insert(issues, `{instance:GetFullName()}: invalid ArtAssetId`)
			continue
		end
		if type(stateId) ~= "string" or not STATES[stateId] then
			table.insert(issues, `{instance:GetFullName()}: invalid ArtState`)
			continue
		end
		if not APPLICABLE_STATES[assetId][stateId] then
			table.insert(
				issues,
				`{instance:GetFullName()}: ArtState is not applicable to {assetId}`
			)
			continue
		end
		if not (instance:IsA("Model") or instance:IsA("BasePart")) then
			table.insert(issues, `{instance:GetFullName()}: expected Model or BasePart`)
			continue
		end
		local sourceSha256 = instance:GetAttribute("ArtSourceSha256")
		if not isSha256(sourceSha256) then
			table.insert(
				issues,
				`{instance:GetFullName()}: ArtSourceSha256 must be a lowercase 64-character SHA-256`
			)
			continue
		end
		local territoryFolder = ensureFolder(root, territory)
		local assetFolder = ensureFolder(territoryFolder, assetId)
		local clone: Instance = instance:Clone()
		clone.Name = stateId
		local styleResult = styleClone(clone, territory, territoryStyles)
		if not styleResult.ok then
			for _, issue in styleResult.issues do
				table.insert(issues, `{instance:GetFullName()}: {issue}`)
			end
			clone:Destroy()
			continue
		end
		hitboxCount += createHitbox(clone, assetId)
		local existing = assetFolder:FindFirstChild(stateId)
		if existing then
			existing:Destroy()
		end
		clone.Parent = assetFolder
		styledMeshCount += styleResult.meshCount
		table.insert(staged, `{territory}/{assetId}/{stateId}`)
	end
	return {
		ok = #issues == 0,
		staged = staged,
		styledMeshCount = styledMeshCount,
		hitboxCount = hitboxCount,
		issues = issues,
	}
end

return table.freeze(AssetKitStager)
