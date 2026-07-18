--!strict

local HttpService = game:GetService("HttpService")
local ServerStorage = game:GetService("ServerStorage")
local Workspace = game:GetService("Workspace")

local PerformanceBenchmarkBuilder = {}

local ASSET_ROOT_NAME = "ArtDirectionAssetKit"
local CONDITIONS_ROOT_NAME = "ArtDirectionPerformanceConditions"
local RIG_NAME = "ArtDirectionPerformanceBenchmark"
local ISOLATION_HEIGHT_STUDS = 4000
local ASSET_IDS = { "barricade", "enemy_standard" }
local COPY_COUNTS = { 30, 100 }

local function setBenchmarkPartProperties(root: Instance)
	if root:IsA("BasePart") then
		root.Anchored = true
		root.CanCollide = false
		root.CanQuery = false
		root.CanTouch = false
	end
	for _, descendant in root:GetDescendants() do
		if descendant:IsA("BasePart") then
			-- The simulator benchmark compares render cost. Production collision
			-- proxies remain in the staged kit and Golden Scene, but fully invisible
			-- parts must not become hidden render-benchmark overhead.
			if descendant.Transparency >= 1 then
				descendant:Destroy()
				continue
			end
			descendant.Anchored = true
			descendant.CanCollide = false
			descendant.CanQuery = false
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
		error(`Unsupported benchmark asset type {root.ClassName}`)
	end
end

local function findSource(territoryId: string, assetId: string): Instance?
	local assetRoot = ServerStorage:FindFirstChild(ASSET_ROOT_NAME)
	local territory = assetRoot and assetRoot:FindFirstChild(territoryId)
	local asset = territory and territory:FindFirstChild(assetId)
	return asset and asset:FindFirstChild("intact")
end

local function makeGraybox(
	parent: Instance,
	assetId: string,
	index: number,
	size: Vector3,
	cframe: CFrame
): Part
	local part = Instance.new("Part")
	part.Name = string.format("%s_graybox_%03d", assetId, index)
	part.Anchored = true
	part.CanCollide = false
	part.CanQuery = false
	part.CanTouch = false
	part.CastShadow = true
	part.Material = Enum.Material.SmoothPlastic
	part.Color = Color3.fromRGB(128, 128, 128)
	part.Size = size
	part.CFrame = cframe * CFrame.new(0, size.Y / 2, 0)
	part:SetAttribute("ArtBenchmarkCondition", "graybox")
	part:SetAttribute("ArtAssetId", assetId)
	part.Parent = parent
	return part
end

local function makeCandidate(
	parent: Instance,
	source: Instance,
	assetId: string,
	index: number,
	cframe: CFrame
): Instance
	local clone = source:Clone()
	clone.Name = string.format("%s_candidate_%03d", assetId, index)
	clone:SetAttribute("ArtBenchmarkCondition", "candidate")
	clone:SetAttribute("ArtAssetId", assetId)
	setBenchmarkPartProperties(clone)
	clone.Parent = parent
	pivotTo(clone, cframe)
	return clone
end

local function conditionName(conditionId: string, copyCount: number): string
	return `{conditionId}_{copyCount}`
end

local function layoutCFrame(assetGroupIndex: number, index: number, copyCount: number): CFrame
	local columns = if copyCount == 30 then 6 else 10
	local spacing = 10
	local rows = math.ceil(copyCount / columns)
	local row = math.floor((index - 1) / columns)
	local column = (index - 1) % columns
	local x = (column - (columns - 1) / 2) * spacing
	local groupDepth = rows * spacing + 18
	local z = (assetGroupIndex - 1) * groupDepth + row * spacing
	return CFrame.new(x, ISOLATION_HEIGHT_STUDS, z)
end

local function buildCondition(
	conditionsRoot: Instance,
	territoryId: string,
	conditionId: string,
	copyCount: number,
	config: any
): ({ string }, number, number)
	local condition = Instance.new("Model")
	condition.Name = conditionName(conditionId, copyCount)
	condition.ModelStreamingMode = Enum.ModelStreamingMode.Persistent
	condition:SetAttribute("ArtBenchmarkCondition", conditionId)
	condition:SetAttribute("ArtBenchmarkCopyCount", copyCount)
	condition:SetAttribute("ArtTerritory", territoryId)
	condition.Parent = conditionsRoot

	local missingSources = {}
	local assetInstances = 0
	local baseParts = 0
	for assetGroupIndex, assetId in ASSET_IDS do
		local source = findSource(territoryId, assetId)
		local spec = config.calibrationKit.assets[assetId]
		local size =
			Vector3.new(spec.dimensions.width, spec.dimensions.height, spec.dimensions.depth)
		local group = Instance.new("Folder")
		group.Name = `Benchmark_{assetId}_{copyCount}`
		group.Parent = condition
		if conditionId == "candidate" and not source then
			table.insert(missingSources, `{territoryId}/{assetId}/intact`)
		else
			for index = 1, copyCount do
				local cframe = layoutCFrame(assetGroupIndex, index, copyCount)
				local instance: Instance
				if conditionId == "candidate" then
					instance = makeCandidate(group, source :: Instance, assetId, index, cframe)
				else
					instance = makeGraybox(group, assetId, index, size, cframe)
				end
				assetInstances += 1
				if instance:IsA("BasePart") then
					baseParts += 1
				end
				for _, descendant in instance:GetDescendants() do
					if descendant:IsA("BasePart") then
						baseParts += 1
					end
				end
			end
		end
	end
	condition:SetAttribute("ArtBenchmarkAssetInstances", assetInstances)
	condition:SetAttribute("ArtBenchmarkBaseParts", baseParts)
	return missingSources, assetInstances, baseParts
end

local function makeRigPart(
	parent: Instance,
	name: string,
	size: Vector3,
	cframe: CFrame,
	color: Color3
): Part
	local part = Instance.new("Part")
	part.Name = name
	part.Anchored = true
	part.CanCollide = false
	part.CanQuery = false
	part.CanTouch = false
	part.CastShadow = false
	part.Material = Enum.Material.SmoothPlastic
	part.Color = color
	part.Size = size
	part.CFrame = cframe
	part.Parent = parent
	return part
end

local function createRig(territoryId: string): Model
	local previous = Workspace:FindFirstChild(RIG_NAME)
	if previous then
		previous:Destroy()
	end
	local rig = Instance.new("Model")
	rig.Name = RIG_NAME
	rig.ModelStreamingMode = Enum.ModelStreamingMode.Persistent
	rig:SetAttribute("ArtTerritory", territoryId)
	rig:SetAttribute("ArtBenchmarkIsolationY", ISOLATION_HEIGHT_STUDS)
	rig:SetAttribute("ArtBenchmarkProtocolVersion", "1.0.0")
	rig:SetAttribute("ArtBenchmarkSessionId", HttpService:GenerateGUID(false))
	rig.Parent = Workspace
	makeRigPart(
		rig,
		"BenchmarkGround",
		Vector3.new(150, 0.2, 250),
		CFrame.new(0, ISOLATION_HEIGHT_STUDS - 0.11, 48),
		Color3.fromRGB(58, 68, 82)
	)
	local cameras = Instance.new("Folder")
	cameras.Name = "Cameras"
	cameras.Parent = rig
	for _, copyCount in COPY_COUNTS do
		local targetZ = if copyCount == 30 then 35 else 55
		local distance = if copyCount == 30 then 95 else 145
		local target = Vector3.new(0, ISOLATION_HEIGHT_STUDS + 2.5, targetZ)
		local position = target + Vector3.new(distance * 0.58, distance * 0.42, -distance)
		local marker = makeRigPart(
			cameras,
			`Stress_{copyCount}`,
			Vector3.new(0.2, 0.2, 0.2),
			CFrame.lookAt(position, target, Vector3.yAxis),
			Color3.new(1, 1, 1)
		)
		marker.Transparency = 1
		marker:SetAttribute("FieldOfView", 70)
	end
	return rig
end

local function findCondition(conditionId: string, copyCount: number): Instance?
	local name = conditionName(conditionId, copyCount)
	local inWorkspace = Workspace:FindFirstChild(name)
	if inWorkspace then
		return inWorkspace
	end
	local root = ServerStorage:FindFirstChild(CONDITIONS_ROOT_NAME)
	return root and root:FindFirstChild(name)
end

function PerformanceBenchmarkBuilder.build(territoryId: string, config: any): any
	local previousRoot = ServerStorage:FindFirstChild(CONDITIONS_ROOT_NAME)
	if previousRoot then
		previousRoot:Destroy()
	end
	for _, conditionId in { "graybox", "candidate" } do
		for _, copyCount in COPY_COUNTS do
			local active = Workspace:FindFirstChild(conditionName(conditionId, copyCount))
			if active then
				active:Destroy()
			end
		end
	end

	local conditionsRoot = Instance.new("Folder")
	conditionsRoot.Name = CONDITIONS_ROOT_NAME
	conditionsRoot:SetAttribute("ArtTerritory", territoryId)
	conditionsRoot:SetAttribute("ArtBenchmarkProtocolVersion", "1.0.0")
	conditionsRoot.Parent = ServerStorage

	local missingSources = {}
	local conditions = {}
	for _, copyCount in COPY_COUNTS do
		for _, conditionId in { "graybox", "candidate" } do
			local missing, assetInstances, baseParts =
				buildCondition(conditionsRoot, territoryId, conditionId, copyCount, config)
			for _, path in missing do
				table.insert(missingSources, path)
			end
			table.insert(conditions, {
				conditionId = conditionId,
				copyCount = copyCount,
				assetInstances = assetInstances,
				baseParts = baseParts,
			})
		end
	end
	local rig = createRig(territoryId)
	return {
		ok = #missingSources == 0,
		code = if #missingSources == 0 then "PASS" else "MISSING_ASSET_SOURCES",
		rig = rig,
		conditionsRoot = conditionsRoot,
		conditions = conditions,
		missingSources = missingSources,
	}
end

function PerformanceBenchmarkBuilder.activate(conditionId: string, copyCount: number): any
	assert(conditionId == "graybox" or conditionId == "candidate", "Unknown benchmark condition")
	assert(copyCount == 30 or copyCount == 100, "Benchmark copy count must be 30 or 100")
	local conditionsRoot = ServerStorage:FindFirstChild(CONDITIONS_ROOT_NAME)
	assert(conditionsRoot, "Performance benchmark conditions are not built")
	for _, candidateCondition in { "graybox", "candidate" } do
		for _, candidateCount in COPY_COUNTS do
			local active =
				Workspace:FindFirstChild(conditionName(candidateCondition, candidateCount))
			if active then
				active.Parent = conditionsRoot
			end
		end
	end
	local target = findCondition(conditionId, copyCount)
	assert(target, `Missing benchmark condition {conditionName(conditionId, copyCount)}`)
	target.Parent = Workspace
	local rig = Workspace:FindFirstChild(RIG_NAME)
	assert(rig, "Performance benchmark rig is missing")
	rig:SetAttribute("ArtBenchmarkActiveCondition", conditionId)
	rig:SetAttribute("ArtBenchmarkActiveCopyCount", copyCount)
	rig:SetAttribute("ArtBenchmarkActivationId", HttpService:GenerateGUID(false))
	return {
		ok = true,
		conditionId = conditionId,
		copyCount = copyCount,
		assetInstances = target:GetAttribute("ArtBenchmarkAssetInstances"),
		baseParts = target:GetAttribute("ArtBenchmarkBaseParts"),
		activationId = rig:GetAttribute("ArtBenchmarkActivationId"),
	}
end

function PerformanceBenchmarkBuilder.deactivate(): any
	local conditionsRoot = ServerStorage:FindFirstChild(CONDITIONS_ROOT_NAME)
	if not conditionsRoot then
		return { ok = false, code = "BENCHMARK_NOT_BUILT" }
	end
	for _, conditionId in { "graybox", "candidate" } do
		for _, copyCount in COPY_COUNTS do
			local active = Workspace:FindFirstChild(conditionName(conditionId, copyCount))
			if active then
				active.Parent = conditionsRoot
			end
		end
	end
	local rig = Workspace:FindFirstChild(RIG_NAME)
	if rig then
		rig:SetAttribute("ArtBenchmarkActiveCondition", nil)
		rig:SetAttribute("ArtBenchmarkActiveCopyCount", nil)
	end
	return { ok = true }
end

return table.freeze(PerformanceBenchmarkBuilder)
