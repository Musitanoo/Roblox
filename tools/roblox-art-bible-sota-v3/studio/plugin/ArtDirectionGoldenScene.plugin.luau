--!strict

-- Expected plugin model hierarchy:
-- ArtDirectionGoldenScene.plugin.luau
-- ├── Generated/ArtDirectionConfig
-- ├── Generated/{LightingProfiles,TerritoryStyles}
-- └── Src/{GoldenSceneBuilder,GoldenSceneValidator,LightingProfileService,AssetKitStager}

local ChangeHistoryService = game:GetService("ChangeHistoryService")
local Selection = game:GetService("Selection")

local generated = script:WaitForChild("Generated")
local src = script:WaitForChild("Src")
local Builder = require(src:WaitForChild("GoldenSceneBuilder"))
local Config = require(generated:WaitForChild("ArtDirectionConfig"))
local LightingProfileService = require(src:WaitForChild("LightingProfileService"))
local LightingProfiles = require(generated:WaitForChild("LightingProfiles"))
local PerformanceBenchmarkBuilder = require(src:WaitForChild("PerformanceBenchmarkBuilder"))
local Stager = require(src:WaitForChild("AssetKitStager"))
local TerritoryStyles = require(generated:WaitForChild("TerritoryStyles"))
local Validator = require(src:WaitForChild("GoldenSceneValidator"))

local toolbar = plugin:CreateToolbar("Art Direction SOTA")
local stageButton = toolbar:CreateButton("Stage selected", "Stage selected attributed assets", "")
local buildA = toolbar:CreateButton("Build A", "Build Industrial Toy Defense Golden Scene", "")
local buildB = toolbar:CreateButton("Build B", "Build Salvaged Frontier Golden Scene", "")
local buildC = toolbar:CreateButton("Build C", "Build Clean Tactical Diorama Golden Scene", "")
local validateButton = toolbar:CreateButton("Validate", "Validate current Golden Scene", "")
local benchmarkButton = toolbar:CreateButton(
	"Build Perf",
	"Build isolated 30/100 graybox and candidate benchmark conditions",
	""
)
local lightingButtons = {
	Lighting_Gameplay_Default = toolbar:CreateButton(
		"Light Game",
		"Apply and record Gameplay lighting",
		""
	),
	Lighting_HighContrast = toolbar:CreateButton(
		"Light Contrast",
		"Apply and record High Contrast lighting",
		""
	),
	Lighting_Adverse_Night = toolbar:CreateButton(
		"Light Night",
		"Apply and record Adverse Night lighting",
		""
	),
	Lighting_Neutral_QA = toolbar:CreateButton(
		"Light QA",
		"Apply and record Neutral QA lighting",
		""
	),
}

local function record(name: string, callback: () -> ())
	local recording = ChangeHistoryService:TryBeginRecording(name, name)
	if not recording then
		warn(`Could not begin ChangeHistory recording: {name}`)
		return
	end
	local callResult = table.pack(pcall(callback))
	local ok = callResult[1]
	ChangeHistoryService:FinishRecording(
		recording,
		if ok then Enum.FinishRecordingOperation.Commit else Enum.FinishRecordingOperation.Cancel
	)
	if not ok then
		error(tostring(callResult[2]))
	end
end

stageButton.Click:Connect(function()
	record("Stage art-direction assets", function()
		local result = Stager.stage(Selection:Get(), TerritoryStyles)
		if not result.ok then
			error(table.concat(result.issues, "\n"))
		end
		print(`Staged {#result.staged} assets.`)
	end)
end)

local function build(territoryId: string)
	record(`Build Golden Scene {territoryId}`, function()
		local result = Builder.build(territoryId, Config, { allowPlaceholders = false })
		if not result.ok then
			error(table.concat(result.missingSources, "\n"))
		end
	end)
end

buildA.Click:Connect(function()
	build("industrial-toy-defense")
end)
buildB.Click:Connect(function()
	build("salvaged-frontier")
end)
buildC.Click:Connect(function()
	build("clean-tactical-diorama")
end)

for profileId, button in lightingButtons do
	button.Click:Connect(function()
		record(`Audit lighting {profileId}`, function()
			local scene = workspace:FindFirstChild("ArtDirectionGoldenScene")
			if not scene then
				error("Workspace.ArtDirectionGoldenScene is missing")
			end
			local result = LightingProfileService.applyAndRecord(profileId, LightingProfiles, scene)
			if not result.ok then
				error(table.concat(result.issues, "\n"))
			end
			print(`Recorded sequential lighting evidence: {profileId}`)
		end)
	end)
end

validateButton.Click:Connect(function()
	local scene = workspace:FindFirstChild("ArtDirectionGoldenScene")
	if not scene then
		error("Workspace.ArtDirectionGoldenScene is missing")
	end
	local territoryId = scene:GetAttribute("ArtTerritory")
	if type(territoryId) ~= "string" then
		error("Golden Scene ArtTerritory attribute is missing")
	end
	local report = Validator.validate(territoryId, Config, LightingProfileService, LightingProfiles)
	if report.status ~= "PASS" then
		warn(table.concat(report.issues, "\n"))
	end
end)

benchmarkButton.Click:Connect(function()
	record("Build art-direction performance benchmark", function()
		local scene = workspace:FindFirstChild("ArtDirectionGoldenScene")
		if not scene then
			error("Workspace.ArtDirectionGoldenScene is missing")
		end
		local territoryId = scene:GetAttribute("ArtTerritory")
		if type(territoryId) ~= "string" then
			error("Golden Scene ArtTerritory attribute is missing")
		end
		local result = PerformanceBenchmarkBuilder.build(territoryId, Config)
		if not result.ok then
			error(table.concat(result.missingSources, "\n"))
		end
		print(`Built isolated A/B performance benchmark for {territoryId}.`)
	end)
end)
