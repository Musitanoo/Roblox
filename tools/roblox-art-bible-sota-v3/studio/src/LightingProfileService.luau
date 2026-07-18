--!strict

-- Applies only script-writable Lighting properties. LightingStyle and
-- PrioritizeLightingQuality are verified as manual Studio preconditions.

local HttpService = game:GetService("HttpService")
local Lighting = game:GetService("Lighting")

local LightingProfileService = {}

local PROTECTED_PROPERTIES = {
	LightingStyle = true,
	PrioritizeLightingQuality = true,
}

local COLOR_PROPERTIES = {
	Ambient = true,
	OutdoorAmbient = true,
	ColorShift_Top = true,
	ColorShift_Bottom = true,
	Color = true,
	Decay = true,
	TintColor = true,
}

local function toColor3(value: any): Color3
	assert(type(value) == "table" and #value == 3, "Expected RGB array")
	return Color3.fromRGB(value[1], value[2], value[3])
end

local function normalizeExpected(propertyName: string, value: any): any
	if COLOR_PROPERTIES[propertyName] then
		return toColor3(value)
	end
	return value
end

local function enumName(value: any): string
	if typeof(value) == "EnumItem" then
		return (value :: EnumItem).Name
	end
	return tostring(value)
end

local function readProperty(instance: Instance, propertyName: string): (boolean, any)
	local ok, value = pcall(function()
		return (instance :: any)[propertyName]
	end)
	return ok, value
end

local function setProperty(instance: Instance, propertyName: string, value: any): (boolean, string?)
	if PROTECTED_PROPERTIES[propertyName] then
		return false, `Protected property {propertyName} cannot be set by this service.`
	end
	local expected = normalizeExpected(propertyName, value)
	local ok, err = pcall(function()
		(instance :: any)[propertyName] = expected
	end)
	if not ok then
		return false, tostring(err)
	end
	return true, nil
end

local function valuesEqual(actual: any, expected: any, tolerance: number): boolean
	if typeof(expected) == "Color3" and typeof(actual) == "Color3" then
		local a = actual :: Color3
		local e = expected :: Color3
		return math.abs(a.R - e.R) <= (1 / 255)
			and math.abs(a.G - e.G) <= (1 / 255)
			and math.abs(a.B - e.B) <= (1 / 255)
	end
	if type(expected) == "number" and type(actual) == "number" then
		return math.abs(actual - expected) <= tolerance
	end
	return actual == expected
end

local function ensureEffect(className: string, name: string): Instance
	local existing = Lighting:FindFirstChild(name)
	if existing and existing.ClassName ~= className then
		existing:Destroy()
		existing = nil
	end
	if existing then
		return existing
	end
	local effect = Instance.new(className)
	effect.Name = name
	effect.Parent = Lighting
	return effect
end

function LightingProfileService.verifyPreconditions(profileId: string, profilesDocument: any): any
	local profile = profilesDocument.profiles[profileId]
	if not profile then
		return { ok = false, code = "UNKNOWN_PROFILE", issues = { `Unknown profile {profileId}` } }
	end
	local issues = {}
	for propertyName, expected in profile.studioManualPreconditions do
		local ok, actual = readProperty(Lighting, propertyName)
		if not ok then
			table.insert(
				issues,
				`Cannot read protected Lighting.{propertyName}: {tostring(actual)}`
			)
		elseif propertyName == "LightingStyle" then
			if enumName(actual) ~= expected then
				table.insert(
					issues,
					`LightingStyle is {enumName(actual)}; expected {expected}. Configure it manually in Studio.`
				)
			end
		elseif actual ~= expected then
			table.insert(
				issues,
				`Lighting.{propertyName} is {tostring(actual)}; expected {tostring(expected)}. Configure it manually in Studio.`
			)
		end
	end
	return {
		ok = #issues == 0,
		code = if #issues == 0 then "PASS" else "READ_ONLY_PRECONDITION_MISMATCH",
		issues = issues,
	}
end

function LightingProfileService.apply(profileId: string, profilesDocument: any): any
	local profile = profilesDocument.profiles[profileId]
	if not profile then
		return { ok = false, code = "UNKNOWN_PROFILE", issues = { `Unknown profile {profileId}` } }
	end

	local preconditions = LightingProfileService.verifyPreconditions(profileId, profilesDocument)
	if not preconditions.ok then
		return preconditions
	end

	local targets = {
		Lighting = Lighting,
		Atmosphere = ensureEffect("Atmosphere", "ArtDirection_Atmosphere"),
		ColorCorrectionEffect = ensureEffect(
			"ColorCorrectionEffect",
			"ArtDirection_ColorCorrection"
		),
		BloomEffect = ensureEffect("BloomEffect", "ArtDirection_Bloom"),
	}
	local issues = {}
	for sectionName, properties in profile.scriptMutable do
		local target = targets[sectionName]
		if not target then
			table.insert(issues, `Unknown mutable section {sectionName}`)
			continue
		end
		for propertyName, rawValue in properties do
			local ok, err = setProperty(target, propertyName, rawValue)
			if not ok then
				table.insert(issues, `{sectionName}.{propertyName}: {err}`)
			end
		end
	end
	if #issues > 0 then
		return { ok = false, code = "MUTATION_FAILED", issues = issues }
	end

	local tolerance = profile.readbackTolerance.numberAbsolute
	for sectionName, properties in profile.scriptMutable do
		local target = targets[sectionName]
		for propertyName, rawValue in properties do
			local expected = normalizeExpected(propertyName, rawValue)
			local ok, actual = readProperty(target, propertyName)
			if not ok then
				table.insert(issues, `Readback failed for {sectionName}.{propertyName}`)
			elseif not valuesEqual(actual, expected, tolerance) then
				table.insert(
					issues,
					`Readback mismatch for {sectionName}.{propertyName}: got {tostring(actual)}, expected {tostring(
						expected
					)}`
				)
			end
		end
	end

	return {
		ok = #issues == 0,
		code = if #issues == 0 then "PASS" else "READBACK_MISMATCH",
		profileId = profileId,
		issues = issues,
	}
end

function LightingProfileService.applyAndRecord(
	profileId: string,
	profilesDocument: any,
	scene: Instance
): any
	local territoryId = scene:GetAttribute("ArtTerritory")
	local sceneSessionId = scene:GetAttribute("ArtSceneSessionId")
	local profilesDigest = profilesDocument.sourceDigest
	if
		type(territoryId) ~= "string"
		or type(sceneSessionId) ~= "string"
		or type(profilesDigest) ~= "string"
		or #profilesDigest ~= 64
	then
		return {
			ok = false,
			code = "EVIDENCE_STALE",
			profileId = profileId,
			issues = {
				"Golden Scene identity is missing; rebuild the scene before lighting audit.",
			},
		}
	end
	local result = LightingProfileService.apply(profileId, profilesDocument)
	local rootInstance = scene:FindFirstChild("LightingEvidence")
	local root: Folder
	if rootInstance and rootInstance:IsA("Folder") then
		root = rootInstance
	else
		if rootInstance then
			rootInstance:Destroy()
		end
		root = Instance.new("Folder")
		root.Name = "LightingEvidence"
		root.Parent = scene
	end
	local existing = root:FindFirstChild(profileId)
	if existing then
		existing:Destroy()
	end
	local evidence = Instance.new("Folder")
	evidence.Name = profileId
	evidence:SetAttribute("ProfileId", profileId)
	evidence:SetAttribute("TerritoryId", territoryId)
	evidence:SetAttribute("SceneSessionId", sceneSessionId)
	evidence:SetAttribute("ProfilesDigest", profilesDigest)
	evidence:SetAttribute("CapturedAtUnix", os.time())
	evidence:SetAttribute("Ok", result.ok == true)
	evidence:SetAttribute("Code", result.code)
	evidence:SetAttribute("IssuesJson", HttpService:JSONEncode(result.issues or {}))
	evidence.Parent = root
	return result
end

function LightingProfileService.collectEvidence(
	scene: Instance,
	profileIds: { string },
	profilesDocument: any
): any
	local results: { [string]: any } = {}
	local root = scene:FindFirstChild("LightingEvidence")
	local territoryId = scene:GetAttribute("ArtTerritory")
	local sceneSessionId = scene:GetAttribute("ArtSceneSessionId")
	local profilesDigest = profilesDocument.sourceDigest
	for _, profileId in profileIds do
		local evidence = root and root:FindFirstChild(profileId)
		if not evidence then
			results[profileId] = {
				ok = false,
				code = "EVIDENCE_MISSING",
				profileId = profileId,
				evidenceFresh = false,
				capturedAtUnix = nil,
				issues = { `No sequential lighting evidence recorded for {profileId}.` },
			}
			continue
		end
		local fresh = type(sceneSessionId) == "string"
			and type(profilesDigest) == "string"
			and evidence:GetAttribute("SceneSessionId") == sceneSessionId
			and evidence:GetAttribute("ProfilesDigest") == profilesDigest
			and evidence:GetAttribute("TerritoryId") == territoryId
			and evidence:GetAttribute("ProfileId") == profileId
		local issues: { string } = {}
		local issuesAttribute = evidence:GetAttribute("IssuesJson")
		local issuesJson = if type(issuesAttribute) == "string" then issuesAttribute else "[]"
		local okDecode, decoded = pcall(function()
			return HttpService:JSONDecode(issuesJson)
		end)
		if okDecode and type(decoded) == "table" then
			issues = decoded
		else
			table.insert(issues, "Lighting evidence issue payload is invalid.")
		end
		if not fresh then
			table.insert(issues, "Lighting evidence belongs to another Golden Scene session.")
		end
		local codeAttribute = evidence:GetAttribute("Code")
		local code = if type(codeAttribute) == "string" then codeAttribute else "EVIDENCE_STALE"
		local capturedAttribute = evidence:GetAttribute("CapturedAtUnix")
		local capturedAtUnix: number? = if type(capturedAttribute) == "number"
			then capturedAttribute
			else nil
		results[profileId] = {
			ok = fresh and evidence:GetAttribute("Ok") == true,
			code = if fresh then code else "EVIDENCE_STALE",
			profileId = profileId,
			evidenceFresh = fresh,
			capturedAtUnix = capturedAtUnix,
			issues = issues,
		}
	end
	return results
end

return table.freeze(LightingProfileService)
