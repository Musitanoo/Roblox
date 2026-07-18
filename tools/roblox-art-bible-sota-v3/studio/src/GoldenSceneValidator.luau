--!strict

local HttpService = game:GetService("HttpService")
local ServerStorage = game:GetService("ServerStorage")
local Workspace = game:GetService("Workspace")

local GoldenSceneValidator = {}

local REQUIRED_ZONES = {
	"Zone_Isolated_Light",
	"Zone_Isolated_Dark",
	"Zone_States",
	"Zone_Stress_30",
	"Zone_Stress_100",
	"Zone_Mixed_Gameplay",
	"Zone_Graybox_Reference",
	"ValidationCameras",
	"ReferenceDecor",
}
local ASSET_IDS =
	{ "barricade", "objective_core", "enemy_standard", "floor_module", "damage_effect" }
local STATE_IDS_BY_ASSET = {
	barricade = { "intact", "damaged", "critical" },
	objective_core = { "intact", "damaged", "critical" },
	enemy_standard = { "intact", "damaged", "critical" },
	floor_module = { "intact", "damaged" },
	damage_effect = { "damaged", "critical" },
}
local CAMERA_IDS = { "near", "mid", "far", "front", "back", "three_quarter" }
local PROFILE_IDS = {
	"Lighting_Gameplay_Default",
	"Lighting_HighContrast",
	"Lighting_Adverse_Night",
	"Lighting_Neutral_QA",
}
local STRESS_IDS = {
	"Stress_barricade_30",
	"Stress_enemy_standard_30",
	"Stress_barricade_100",
	"Stress_enemy_standard_100",
}

local function isSha256(value: any): boolean
	return type(value) == "string" and #value == 64 and string.match(value, "^[0-9a-f]+$") ~= nil
end

local function instanceBounds(instance: Instance): Vector3?
	if instance:IsA("Model") then
		local _, size = instance:GetBoundingBox()
		return size
	elseif instance:IsA("BasePart") then
		return instance.Size
	end
	return nil
end

local function near(a: number, b: number, tolerance: number): boolean
	return math.abs(a - b) <= tolerance
end

local function assetSignature(instance: Instance): (string, number)
	local entries = {}
	local meshPartCount = 0
	local candidates = { instance }
	for _, descendant in instance:GetDescendants() do
		table.insert(candidates, descendant)
	end
	for _, candidate in candidates do
		if candidate:IsA("MeshPart") then
			meshPartCount += 1
			table.insert(entries, `MeshPart|{candidate.MeshId}|{candidate.TextureID}`)
		elseif candidate:IsA("SurfaceAppearance") then
			table.insert(
				entries,
				`SurfaceAppearance|{candidate.ColorMap}|{candidate.NormalMap}|{candidate.RoughnessMap}|{candidate.MetalnessMap}`
			)
		end
	end
	table.sort(entries)
	return table.concat(entries, "\n"), meshPartCount
end

local function validateStressGroup(group: Instance): any
	local children = group:GetChildren()
	local expected = group:GetAttribute("ExpectedCount") or 30
	local issues = {}
	if #children ~= expected then
		table.insert(issues, `{group.Name} has {#children} clones; expected {expected}`)
	end
	local signatures = {}
	local sourceHashes = {}
	local meshPartCount = 0
	for _, child in children do
		local signature, childMeshPartCount = assetSignature(child)
		meshPartCount += childMeshPartCount
		if childMeshPartCount == 0 or signature == "" then
			table.insert(
				issues,
				`{child:GetFullName()} has no MeshPart identity and cannot prove instancing reuse`
			)
		else
			signatures[signature] = true
		end
		local sourceSha256 = child:GetAttribute("ArtSourceSha256")
		if not isSha256(sourceSha256) then
			table.insert(issues, `{child:GetFullName()} lacks a valid ArtSourceSha256`)
		else
			sourceHashes[sourceSha256] = true
		end
	end
	local signatureCount = 0
	for _ in signatures do
		signatureCount += 1
	end
	local sourceSha256Count = 0
	for _ in sourceHashes do
		sourceSha256Count += 1
	end
	if signatureCount ~= 1 then
		table.insert(
			issues,
			`{group.Name} contains {signatureCount} distinct MeshId/texture signatures; expected 1`
		)
	end
	if sourceSha256Count ~= 1 then
		table.insert(
			issues,
			`{group.Name} contains {sourceSha256Count} distinct source SHA-256 values; expected 1`
		)
	end
	return {
		pass = #issues == 0,
		observedCount = #children,
		distinctSignatures = signatureCount,
		meshPartCount = meshPartCount,
		sourceSha256Count = sourceSha256Count,
		issues = issues,
	}
end

local function emptyAssetChecks(reason: string): any
	local result = {}
	for _, assetId in ASSET_IDS do
		result[assetId] = {}
		for _, stateId in STATE_IDS_BY_ASSET[assetId] do
			result[assetId][stateId] = {
				pass = false,
				reason = reason,
				sourceSha256Present = false,
				sourceIdentityMatches = false,
			}
		end
	end
	return result
end

local function emptyZoneChecks(): any
	local result = {}
	for _, zoneName in REQUIRED_ZONES do
		result[zoneName] = false
	end
	return result
end

local function emptyCameraChecks(): any
	local result = {}
	for _, cameraId in CAMERA_IDS do
		result[cameraId] = false
	end
	return result
end

local function emptyReuseChecks(message: string): any
	local result = {}
	for _, groupId in STRESS_IDS do
		result[groupId] = {
			pass = false,
			observedCount = 0,
			distinctSignatures = 0,
			meshPartCount = 0,
			sourceSha256Count = 0,
			issues = { message },
		}
	end
	return result
end

local function emptyLightingChecks(message: string): any
	local result = {}
	for _, profileId in PROFILE_IDS do
		result[profileId] = {
			ok = false,
			code = "EVIDENCE_MISSING",
			profileId = profileId,
			evidenceFresh = false,
			capturedAtUnix = nil,
			issues = { message },
		}
	end
	return result
end

local function emit(report: any, scene: Instance?): any
	local json = HttpService:JSONEncode(report)
	if scene then
		local existing = scene:FindFirstChild("ValidationReport")
		local value: StringValue
		if existing and existing:IsA("StringValue") then
			value = existing
		else
			if existing then
				existing:Destroy()
			end
			value = Instance.new("StringValue")
			value.Name = "ValidationReport"
			value.Parent = scene
		end
		value.Value = json
	end
	print(json)
	return report
end

local function environmentChecks(): any
	local staging = ServerStorage:FindFirstChild("ArtDirectionStaging")
	return {
		deploymentMarkedStaging = game:GetAttribute("DeploymentEnvironment") == "staging"
			and game:GetAttribute("StagingOnly") == true,
		localConfigComplete = staging ~= nil
			and staging:GetAttribute("LocalConfigComplete") == true,
		savedCloudPlaceVerified = game.PlaceId > 0 and staging ~= nil and staging:GetAttribute(
			"SavedCloudPlaceVerified"
		) == true,
		expectedCreatorMatches = staging ~= nil
			and staging:GetAttribute("ExpectedCreatorMatches") == true,
		creatorAllowlistVerified = staging ~= nil
			and staging:GetAttribute("CreatorAllowlistVerified") == true,
		editModeVerified = staging ~= nil and staging:GetAttribute("EditModeVerified") == true,
	}
end

local function blockedReport(territoryId: string, issue: string): any
	return {
		["$schema"] = "https://roblox-top1.local/schemas/studio-report.schema.json",
		schemaVersion = "3.0.0",
		status = "BLOCKED",
		territoryId = territoryId,
		placeId = nil,
		placeVersion = nil,
		privacy = {
			rawPlaceIdIncluded = false,
			rawCreatorIdIncluded = false,
			rawApiKeyIncluded = false,
		},
		environmentChecks = environmentChecks(),
		generatedAt = os.date("!%Y-%m-%dT%H:%M:%SZ"),
		sceneChecks = {
			scenePresent = false,
			placeholderCount = 0,
			missingSourceCount = 13,
			referenceAvatarPresent = false,
			artTerritoryMatches = false,
			sceneSessionPresent = false,
		},
		zoneChecks = emptyZoneChecks(),
		assetChecks = emptyAssetChecks("scene_missing"),
		reuseChecks = emptyReuseChecks(issue),
		lightingChecks = emptyLightingChecks(issue),
		cameraChecks = emptyCameraChecks(),
		artifacts = {},
		issues = { issue },
	}
end

function GoldenSceneValidator.validate(
	territoryId: string,
	config: any,
	lightingProfileService: any,
	lightingProfiles: any
): any
	local scene = Workspace:FindFirstChild("ArtDirectionGoldenScene")
	if not scene then
		return emit(blockedReport(territoryId, "Workspace.ArtDirectionGoldenScene is missing"), nil)
	end

	local issues = {}
	local zoneChecks = emptyZoneChecks()
	for _, zoneName in REQUIRED_ZONES do
		local exists = scene:FindFirstChild(zoneName) ~= nil
		zoneChecks[zoneName] = exists
		if not exists then
			table.insert(issues, `Missing zone {zoneName}`)
		end
	end
	local placeholderCount = scene:GetAttribute("PlaceholderCount") or 0
	local missingSourceCount = scene:GetAttribute("MissingSourceCount") or 0
	if placeholderCount > 0 then
		table.insert(issues, "Golden Scene contains placeholders and is not valid evidence")
	end
	if missingSourceCount > 0 then
		table.insert(issues, "Golden Scene was built with missing staged sources")
	end
	local avatarPresent = scene:FindFirstChild("ReferenceAvatar_R15") ~= nil
	if not avatarPresent then
		table.insert(issues, "ReferenceAvatar_R15 is missing")
	end
	local artTerritoryMatches = scene:GetAttribute("ArtTerritory") == territoryId
	if not artTerritoryMatches then
		table.insert(issues, "Scene ArtTerritory does not match the requested territory")
	end
	local sceneSessionPresent = type(scene:GetAttribute("ArtSceneSessionId")) == "string"
	if not sceneSessionPresent then
		table.insert(issues, "Scene ArtSceneSessionId is missing")
	end

	local assetChecks = emptyAssetChecks("missing")
	local isolated = scene:FindFirstChild("Zone_Isolated_Light")
	if isolated then
		for _, assetId in ASSET_IDS do
			local assetSpec = config.calibrationKit.assets[assetId]
			local target = assetSpec.dimensions
			local referenceState = assetSpec.requiredStateVariants[1]
			for _, stateId in assetSpec.requiredStateVariants do
				local found: Instance? = nil
				for _, child in isolated:GetChildren() do
					if
						child:GetAttribute("ArtAssetId") == assetId
						and child:GetAttribute("ArtState") == stateId
					then
						found = child
						break
					end
				end
				if not found then
					table.insert(issues, `Missing isolated asset {assetId}/{stateId}`)
				else
					local size = instanceBounds(found)
					local boundsPass = false
					if size then
						if stateId == referenceState then
							boundsPass = near(size.X, target.width, 0.05)
								and near(size.Y, target.height, 0.05)
								and near(size.Z, target.depth, 0.05)
						else
							boundsPass = size.X <= target.width + 0.05
								and size.X >= target.width * 0.55
								and size.Y <= target.height + 0.05
								and size.Y >= target.height * 0.55
								and size.Z <= target.depth + 0.05
								and size.Z >= target.depth * 0.55
						end
					end
					local sourceSha256Present = isSha256(found:GetAttribute("ArtSourceSha256"))
					local sourceIdentityMatches = found:GetAttribute("ArtTerritory") == territoryId
						and found:GetAttribute("ArtAssetId") == assetId
						and found:GetAttribute("ArtState") == stateId
					local pass = boundsPass and sourceSha256Present and sourceIdentityMatches
					local reason: string? = nil
					if not boundsPass then
						reason = "bounds_mismatch"
					elseif not sourceSha256Present then
						reason = "source_identity_missing"
					elseif not sourceIdentityMatches then
						reason = "source_identity_mismatch"
					end
					local check = {
						pass = pass,
						observed = if size then { size.X, size.Y, size.Z } else nil,
						target = { target.width, target.height, target.depth },
						sourceSha256Present = sourceSha256Present,
						sourceIdentityMatches = sourceIdentityMatches,
					}
					if reason then
						check.reason = reason
					end
					assetChecks[assetId][stateId] = check
					if not pass then
						table.insert(
							issues,
							`Asset validation failed for {assetId}/{stateId}: {reason or "unknown"}`
						)
					end
				end
			end
		end
	end

	local reuseChecks = emptyReuseChecks("Stress group missing")
	for _, count in { 30, 100 } do
		local stress = scene:FindFirstChild(`Zone_Stress_{count}`)
		if stress then
			for _, assetId in { "barricade", "enemy_standard" } do
				local groupId = `Stress_{assetId}_{count}`
				local group = stress:FindFirstChild(groupId)
				if group then
					reuseChecks[groupId] = validateStressGroup(group)
					for _, issue in reuseChecks[groupId].issues do
						table.insert(issues, issue)
					end
				else
					table.insert(issues, `Missing stress group {groupId}`)
				end
			end
		end
	end

	local cameraChecks = emptyCameraChecks()
	local cameras = scene:FindFirstChild("ValidationCameras")
	local isolationY = scene:GetAttribute("ArtSceneIsolationY")
	if cameras then
		for _, cameraId in CAMERA_IDS do
			local camera = cameras:FindFirstChild(cameraId)
			local pass = camera ~= nil
				and camera:IsA("Camera")
				and camera.FieldOfViewMode == Enum.FieldOfViewMode.Vertical
				and near(camera.FieldOfView, config.cameraRig.fieldOfView.degrees, 0.01)
				and type(isolationY) == "number"
				and camera.CFrame.Position.Y > isolationY
			cameraChecks[cameraId] = pass
			if not pass then
				table.insert(
					issues,
					`Camera {cameraId} missing, invalid, or outside scene isolation`
				)
			end
		end
	end

	local lightingChecks =
		lightingProfileService.collectEvidence(scene, PROFILE_IDS, lightingProfiles)
	for _, profileId in PROFILE_IDS do
		local result = lightingChecks[profileId]
		if not result.ok then
			for _, issue in result.issues do
				table.insert(issues, `{profileId}: {issue}`)
			end
		end
	end

	local report = {
		["$schema"] = "https://roblox-top1.local/schemas/studio-report.schema.json",
		schemaVersion = "3.0.0",
		status = if #issues == 0 then "PASS" else "FAIL",
		territoryId = territoryId,
		placeId = nil,
		placeVersion = nil,
		privacy = {
			rawPlaceIdIncluded = false,
			rawCreatorIdIncluded = false,
			rawApiKeyIncluded = false,
		},
		environmentChecks = environmentChecks(),
		generatedAt = os.date("!%Y-%m-%dT%H:%M:%SZ"),
		sceneChecks = {
			scenePresent = true,
			placeholderCount = placeholderCount,
			missingSourceCount = missingSourceCount,
			referenceAvatarPresent = avatarPresent,
			artTerritoryMatches = artTerritoryMatches,
			sceneSessionPresent = sceneSessionPresent,
		},
		zoneChecks = zoneChecks,
		assetChecks = assetChecks,
		reuseChecks = reuseChecks,
		lightingChecks = lightingChecks,
		cameraChecks = cameraChecks,
		artifacts = {},
		issues = issues,
	}
	return emit(report, scene)
end

return table.freeze(GoldenSceneValidator)
