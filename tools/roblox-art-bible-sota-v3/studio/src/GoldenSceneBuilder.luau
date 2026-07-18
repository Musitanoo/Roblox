--!strict

local HttpService = game:GetService("HttpService")
local Players = game:GetService("Players")
local ServerStorage = game:GetService("ServerStorage")
local Workspace = game:GetService("Workspace")

local GoldenSceneBuilder = {}

local SCENE_NAME = "ArtDirectionGoldenScene"
local ISOLATION_HEIGHT_STUDS = 2000
local ASSET_ROOT_NAME = "ArtDirectionAssetKit"
local ASSET_IDS =
	{ "barricade", "objective_core", "enemy_standard", "floor_module", "damage_effect" }

local function makePart(
	parent: Instance,
	name: string,
	size: Vector3,
	cframe: CFrame,
	color: Color3,
	transparency: number?
): Part
	local part = Instance.new("Part")
	part.Name = name
	part.Anchored = true
	part.CanCollide = false
	part.CanQuery = false
	part.CanTouch = false
	part.Size = size
	part.CFrame = cframe
	part.Color = color
	part.Material = Enum.Material.SmoothPlastic
	part.Transparency = transparency or 0
	part.Parent = parent
	return part
end

local function colorFromHex(hex: string): Color3
	local value = string.gsub(hex, "#", "")
	return Color3.fromRGB(
		tonumber(string.sub(value, 1, 2), 16) or 0,
		tonumber(string.sub(value, 3, 4), 16) or 0,
		tonumber(string.sub(value, 5, 6), 16) or 0
	)
end

local function setAnchored(root: Instance)
	if root:IsA("BasePart") then
		root.Anchored = true
		root.CanCollide = false
	end
	for _, descendant in root:GetDescendants() do
		if descendant:IsA("BasePart") then
			descendant.Anchored = true
			descendant.CanCollide = false
			descendant.CanTouch = false
		end
	end
end

local function pivotTo(root: Instance, cframe: CFrame)
	if root:IsA("Model") then
		root:PivotTo(cframe)
	elseif root:IsA("BasePart") then
		root.CFrame = cframe
	else
		error(`Unsupported staged asset type {root.ClassName}; expected Model or BasePart`)
	end
end

local function cloneSource(
	source: Instance,
	parent: Instance,
	cframe: CFrame,
	attributes: { [string]: any }
): Instance
	local clone = source:Clone()
	clone.Name = `{attributes.ArtAssetId}_{attributes.ArtState}`
	for key, value in attributes do
		clone:SetAttribute(key, value)
	end
	local sourceSha256 = source:GetAttribute("ArtSourceSha256")
	if sourceSha256 then
		clone:SetAttribute("ArtSourceSha256", sourceSha256)
	end
	setAnchored(clone)
	clone.Parent = parent
	pivotTo(clone, cframe)
	return clone
end

local function findSource(territoryId: string, assetId: string, stateId: string): Instance?
	local root = ServerStorage:FindFirstChild(ASSET_ROOT_NAME)
	local territory = root and root:FindFirstChild(territoryId)
	local asset = territory and territory:FindFirstChild(assetId)
	return asset and asset:FindFirstChild(stateId)
end

local function createPlaceholder(
	parent: Instance,
	assetId: string,
	stateId: string,
	dimensions: any,
	cframe: CFrame,
	color: Color3
): Instance
	local model = Instance.new("Model")
	model.Name = `{assetId}_{stateId}_PLACEHOLDER`
	model:SetAttribute("ArtPlaceholder", true)
	model:SetAttribute("ArtAssetId", assetId)
	model:SetAttribute("ArtState", stateId)
	local size = Vector3.new(dimensions.width, dimensions.height, dimensions.depth)
	local part =
		makePart(model, "PlaceholderBounds", size, CFrame.new(0, size.Y / 2, 0), color, 0.2)
	model.PrimaryPart = part
	model.Parent = parent
	model:PivotTo(cframe)
	return model
end

local function createGrid(parent: Instance, width: number, depth: number)
	local grid = Instance.new("Folder")
	grid.Name = "StudGrid"
	grid.Parent = parent
	local step = 10
	for x = -width / 2, width / 2, step do
		makePart(
			grid,
			`GridX_{x}`,
			Vector3.new(0.04, 0.02, depth),
			CFrame.new(x, 0.011, 0),
			Color3.fromRGB(100, 110, 125),
			0.55
		)
	end
	for z = -depth / 2, depth / 2, step do
		makePart(
			grid,
			`GridZ_{z}`,
			Vector3.new(width, 0.02, 0.04),
			CFrame.new(0, 0.012, z),
			Color3.fromRGB(100, 110, 125),
			0.55
		)
	end
end

local function createReferenceAvatar(parent: Instance, position: Vector3): (Instance?, string?)
	local ok, result = pcall(function()
		local description = Instance.new("HumanoidDescription")
		return Players:CreateHumanoidModelFromDescriptionAsync(
			description,
			Enum.HumanoidRigType.R15
		)
	end)
	if not ok then
		return nil, tostring(result)
	end
	local avatar = result :: Model
	avatar.Name = "ReferenceAvatar_R15"
	setAnchored(avatar)
	avatar.Parent = parent
	avatar:PivotTo(CFrame.new(position))
	return avatar, nil
end

local function cameraCFrame(spec: any): CFrame
	local distance = spec.distanceStuds
	local azimuth = math.rad(spec.azimuthDegrees)
	local elevation = math.rad(spec.elevationDegrees)
	local target = Vector3.new(0, spec.targetHeightStuds, 0)
	local horizontal = distance * math.cos(elevation)
	local position = Vector3.new(
		horizontal * math.sin(azimuth),
		target.Y + distance * math.sin(elevation),
		-horizontal * math.cos(azimuth)
	)
	return CFrame.lookAt(position, target, Vector3.yAxis)
end

local function createCameras(parent: Instance, cameraRig: any)
	local folder = Instance.new("Folder")
	folder.Name = "ValidationCameras"
	folder.Parent = parent
	for cameraId, spec in cameraRig.validationCameras do
		local camera = Instance.new("Camera")
		camera.Name = cameraId
		camera.FieldOfViewMode = Enum.FieldOfViewMode.Vertical
		camera.FieldOfView = cameraRig.fieldOfView.degrees
		camera.CFrame = cameraCFrame(spec)
		camera:SetAttribute("DistanceStuds", spec.distanceStuds)
		camera:SetAttribute("AzimuthDegrees", spec.azimuthDegrees)
		camera:SetAttribute("ElevationDegrees", spec.elevationDegrees)
		camera.Parent = folder
	end
end

local function createDecor(parent: Instance)
	local folder = Instance.new("Folder")
	folder.Name = "ReferenceDecor"
	folder.Parent = parent
	makePart(
		folder,
		"DecorTrunk",
		Vector3.new(1.2, 5, 1.2),
		CFrame.new(66, 2.5, 48),
		Color3.fromRGB(92, 72, 54)
	)
	local crown = makePart(
		folder,
		"DecorCrown",
		Vector3.new(5, 4, 5),
		CFrame.new(66, 6.3, 48),
		Color3.fromRGB(79, 112, 82)
	)
	crown.Shape = Enum.PartType.Ball
	local rock = makePart(
		folder,
		"DecorRock",
		Vector3.new(5, 3, 4),
		CFrame.new(70, 1.5, 36) * CFrame.Angles(0.1, 0.4, 0.05),
		Color3.fromRGB(105, 109, 116)
	)
	rock.Shape = Enum.PartType.Ball
end

local function createStressZone(parent: Instance, territoryId: string, count: number, baseZ: number)
	local stress = Instance.new("Folder")
	stress.Name = `Zone_Stress_{count}`
	stress.Parent = parent
	local columns = if count == 30 then 6 else 10
	local spacing = 10
	for groupIndex, assetId in { "barricade", "enemy_standard" } do
		local source = findSource(territoryId, assetId, "intact")
		local group = Instance.new("Folder")
		group.Name = `Stress_{assetId}_{count}`
		group:SetAttribute("ExpectedCount", count)
		group.Parent = stress
		if source then
			local rows = math.ceil(count / columns)
			local groupZ = baseZ + (groupIndex - 1) * (rows * spacing + 20)
			for index = 1, count do
				local row = math.floor((index - 1) / columns)
				local column = (index - 1) % columns
				local x = (column - (columns - 1) / 2) * spacing
				local z = groupZ + row * spacing
				cloneSource(source, group, CFrame.new(x, 0, z), {
					ArtTerritory = territoryId,
					ArtAssetId = assetId,
					ArtState = "intact",
					ArtZone = `stress_{count}`,
					ArtCloneGroup = `stress_{assetId}_{count}`,
					ArtSourcePath = `{ASSET_ROOT_NAME}/{territoryId}/{assetId}/intact`,
				})
			end
		end
	end
end

function GoldenSceneBuilder.build(territoryId: string, config: any, options: any?): any
	options = options or {}
	local allowPlaceholders = options.allowPlaceholders == true
	local existing = Workspace:FindFirstChild(SCENE_NAME)
	if existing then
		existing:Destroy()
	end
	local scene = Instance.new("Model")
	scene.Name = SCENE_NAME
	scene:SetAttribute("ArtTerritory", territoryId)
	scene:SetAttribute("ArtSceneSessionId", HttpService:GenerateGUID(false))
	scene:SetAttribute("GeneratedAtUnix", os.time())
	scene.Parent = Workspace

	local calibration = config.calibrationKit
	local palette = config.semanticPalette.roles
	local lightColor = colorFromHex(palette.world_neutral_light.hex)
	local darkColor = colorFromHex(palette.world_neutral_dark.hex)
	local sceneSize = calibration.goldenScene.size
	makePart(
		scene,
		"GroundLight",
		Vector3.new(sceneSize.width / 2, 0.4, sceneSize.depth),
		CFrame.new(-sceneSize.width / 4, -0.2, 0),
		lightColor
	)
	makePart(
		scene,
		"GroundDark",
		Vector3.new(sceneSize.width / 2, 0.4, sceneSize.depth),
		CFrame.new(sceneSize.width / 4, -0.2, 0),
		darkColor
	)
	createGrid(scene, sceneSize.width, sceneSize.depth)
	createCameras(scene, config.cameraRig)
	createDecor(scene)

	local avatar, avatarError = createReferenceAvatar(scene, Vector3.new(-70, 0, -58))
	if not avatar then
		scene:SetAttribute("AvatarCreationError", avatarError)
	end

	local missingSources = {}
	local placeholderCount = 0
	local isolatedLight = Instance.new("Folder")
	isolatedLight.Name = "Zone_Isolated_Light"
	isolatedLight.Parent = scene
	local isolatedDark = Instance.new("Folder")
	isolatedDark.Name = "Zone_Isolated_Dark"
	isolatedDark.Parent = scene
	local stateZone = Instance.new("Folder")
	stateZone.Name = "Zone_States"
	stateZone.Parent = scene

	for assetIndex, assetId in ASSET_IDS do
		local assetSpec = calibration.assets[assetId]
		for stateIndex, stateId in assetSpec.requiredStateVariants do
			local source = findSource(territoryId, assetId, stateId)
			if not source then
				table.insert(missingSources, `{territoryId}/{assetId}/{stateId}`)
			end
			local xLight = -62 + (assetIndex - 1) * 13
			local xDark = 10 + (assetIndex - 1) * 13
			local z = -48 + (stateIndex - 1) * 12
			for _, target in
				{
					{
						parent = isolatedLight,
						cframe = CFrame.new(xLight, 0, z),
						zone = "isolated_light",
					},
					{
						parent = isolatedDark,
						cframe = CFrame.new(xDark, 0, z),
						zone = "isolated_dark",
					},
				}
			do
				if source then
					cloneSource(source, target.parent, target.cframe, {
						ArtTerritory = territoryId,
						ArtAssetId = assetId,
						ArtState = stateId,
						ArtZone = target.zone,
						ArtSourcePath = `{ASSET_ROOT_NAME}/{territoryId}/{assetId}/{stateId}`,
					})
				elseif allowPlaceholders then
					createPlaceholder(
						target.parent,
						assetId,
						stateId,
						assetSpec.dimensions,
						target.cframe,
						colorFromHex(palette.disabled.hex)
					)
					placeholderCount += 1
				end
			end
			if assetId == "objective_core" then
				local stateCFrame = CFrame.new(-20 + (stateIndex - 1) * 14, 0, 12)
				if source then
					cloneSource(source, stateZone, stateCFrame, {
						ArtTerritory = territoryId,
						ArtAssetId = assetId,
						ArtState = stateId,
						ArtZone = "states",
						ArtSourcePath = `{ASSET_ROOT_NAME}/{territoryId}/{assetId}/{stateId}`,
					})
				elseif allowPlaceholders then
					createPlaceholder(
						stateZone,
						assetId,
						stateId,
						assetSpec.dimensions,
						stateCFrame,
						colorFromHex(palette.disabled.hex)
					)
					placeholderCount += 1
				end
			end
		end
	end

	for _, count in calibration.goldenScene.stressCopyCounts do
		for _, assetId in { "barricade", "enemy_standard" } do
			if not findSource(territoryId, assetId, "intact") then
				table.insert(
					missingSources,
					`{territoryId}/{assetId}/intact (stress {count} source)`
				)
			end
		end
		createStressZone(scene, territoryId, count, if count == 30 then 80 else 160)
	end

	local mixed = Instance.new("Folder")
	mixed.Name = "Zone_Mixed_Gameplay"
	mixed.Parent = scene
	type MixedItem = { assetId: string, stateId: string, cframe: CFrame }
	local mixedLayout: { MixedItem } = {
		{ assetId = "objective_core", stateId = "damaged", cframe = CFrame.new(0, 0, 52) },
		{ assetId = "barricade", stateId = "intact", cframe = CFrame.new(-10, 0, 42) },
		{ assetId = "barricade", stateId = "critical", cframe = CFrame.new(10, 0, 42) },
		{ assetId = "enemy_standard", stateId = "intact", cframe = CFrame.new(-8, 0, 62) },
		{ assetId = "enemy_standard", stateId = "critical", cframe = CFrame.new(8, 0, 64) },
		{ assetId = "damage_effect", stateId = "critical", cframe = CFrame.new(4, 4, 55) },
	}
	for _, item in mixedLayout do
		local source = findSource(territoryId, item.assetId, item.stateId)
		if source then
			cloneSource(source, mixed, item.cframe, {
				ArtTerritory = territoryId,
				ArtAssetId = item.assetId,
				ArtState = item.stateId,
				ArtZone = "mixed_gameplay",
				ArtSourcePath = `{ASSET_ROOT_NAME}/{territoryId}/{item.assetId}/{item.stateId}`,
			})
		end
	end

	local graybox = Instance.new("Folder")
	graybox.Name = "Zone_Graybox_Reference"
	graybox.Parent = scene
	for index, assetId in ASSET_IDS do
		local dimensions = calibration.assets[assetId].dimensions
		local size = Vector3.new(dimensions.width, dimensions.height, dimensions.depth)
		makePart(
			graybox,
			`Graybox_{assetId}`,
			size,
			CFrame.new(-32 + index * 12, size.Y / 2, -2),
			Color3.fromRGB(128, 128, 128),
			0.15
		)
	end

	-- Keep visual and performance evidence independent from the experience's
	-- unsynced world geometry. Moving the model once also moves validation
	-- cameras and every stress clone without changing local bounds.
	scene:PivotTo(scene:GetPivot() + Vector3.new(0, ISOLATION_HEIGHT_STUDS, 0))
	-- Camera instances are not moved by Model:PivotTo(). Keep the evidence
	-- viewpoints in the same isolated coordinate space as the rendered scene.
	local validationCameras = scene:FindFirstChild("ValidationCameras")
	if validationCameras then
		for _, camera in validationCameras:GetChildren() do
			if camera:IsA("Camera") then
				camera.CFrame += Vector3.new(0, ISOLATION_HEIGHT_STUDS, 0)
			end
		end
	end
	scene:SetAttribute("ArtSceneIsolationY", ISOLATION_HEIGHT_STUDS)

	scene:SetAttribute("MissingSourceCount", #missingSources)
	scene:SetAttribute("PlaceholderCount", placeholderCount)
	return {
		ok = #missingSources == 0 and placeholderCount == 0,
		code = if #missingSources == 0 and placeholderCount == 0
			then "PASS"
			else if allowPlaceholders
				then "PLACEHOLDER_SCENE_NOT_VALID_EVIDENCE"
				else "MISSING_ASSET_SOURCES",
		scene = scene,
		missingSources = missingSources,
		placeholderCount = placeholderCount,
	}
end

return table.freeze(GoldenSceneBuilder)
