--!strict

local ReplicatedStorage = game:GetService("ReplicatedStorage")

type RouteId = "Left" | "Right"
type RouteDefenseState = {
	wallCount: number,
	wallHealth: number,
	slowTrapCount: number,
}
type SpawnMap = { Left: BasePart, Right: BasePart }
type NodeMap = { Left: { BasePart }, Right: { BasePart } }
type ReviewReport = {
	LeftLaneEnemyCount: number,
	RightLaneEnemyCount: number,
	FirstBreachLane: string,
	FirstBreachPadId: string,
}
type RouteConfigType = {
	wallCost: number,
	slowTrapCost: number,
	roamerPreferredChance: number,
	baseTravelCost: { [string]: number },
}

local runtimeRequire = require
local sharedGame = ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Game")
local configFolder = sharedGame:WaitForChild("Config")
local RouteConfig =
	runtimeRequire(configFolder:WaitForChild("RouteConfig") :: ModuleScript) :: RouteConfigType

type DefenseQuery = (routeId: RouteId) -> RouteDefenseState

local RouteService = {}
RouteService.__index = RouteService

export type Service = typeof(setmetatable(
	{} :: {
		_spawns: SpawnMap,
		_nodes: NodeMap,
		_buildPads: Folder,
		_reviewMarkers: Folder,
		_random: Random,
		_nextBruteTie: RouteId,
		_defenseQuery: DefenseQuery?,
	},
	RouteService
))

local function otherRoute(routeId: RouteId): RouteId
	return if routeId == "Left" then "Right" :: RouteId else "Left" :: RouteId
end

local function collectNodes(lane: Folder): { BasePart }
	local nodes: { BasePart } = {}
	for _, child in lane:GetChildren() do
		if child:IsA("BasePart") and string.match(child.Name, "^Node%d%d$") then
			table.insert(nodes, child)
		end
	end
	table.sort(nodes, function(left: BasePart, right: BasePart): boolean
		return left.Name < right.Name
	end)
	assert(#nodes == 5, string.format("%s requires exactly five nodes", lane:GetFullName()))
	return nodes
end

function RouteService.new(prototype: Folder, random: Random?): Service
	local enemySpawns = prototype:FindFirstChild("EnemySpawns")
	local lanes = prototype:FindFirstChild("Lanes")
	local buildPads = prototype:FindFirstChild("BuildPads")
	local reviewMarkers = prototype:FindFirstChild("ReviewMarkers")
	assert(enemySpawns and enemySpawns:IsA("Folder"), "Prototype.EnemySpawns is required")
	assert(lanes and lanes:IsA("Folder"), "Prototype.Lanes is required")
	assert(buildPads and buildPads:IsA("Folder"), "Prototype.BuildPads is required")
	assert(reviewMarkers and reviewMarkers:IsA("Folder"), "Prototype.ReviewMarkers is required")

	local leftSpawn = enemySpawns:FindFirstChild("LeftSpawn")
	local rightSpawn = enemySpawns:FindFirstChild("RightSpawn")
	local leftLane = lanes:FindFirstChild("LeftLane")
	local rightLane = lanes:FindFirstChild("RightLane")
	assert(leftSpawn and leftSpawn:IsA("BasePart"), "LeftSpawn is required")
	assert(rightSpawn and rightSpawn:IsA("BasePart"), "RightSpawn is required")
	assert(leftLane and leftLane:IsA("Folder"), "LeftLane is required")
	assert(rightLane and rightLane:IsA("Folder"), "RightLane is required")

	local self: Service = setmetatable({
		_spawns = { Left = leftSpawn, Right = rightSpawn },
		_nodes = { Left = collectNodes(leftLane), Right = collectNodes(rightLane) },
		_buildPads = buildPads,
		_reviewMarkers = reviewMarkers,
		_random = random or Random.new(),
		_nextBruteTie = "Left" :: RouteId,
		_defenseQuery = nil,
	}, RouteService)
	self:hideReviewMarkers()
	return self
end

function RouteService.setDefenseQuery(self: Service, query: DefenseQuery)
	self._defenseQuery = query
end

function RouteService.getSpawn(self: Service, routeId: RouteId): BasePart
	return self._spawns[routeId]
end

function RouteService.getNodes(self: Service, routeId: RouteId): { BasePart }
	return self._nodes[routeId]
end

function RouteService.getDefenseState(self: Service, routeId: RouteId): RouteDefenseState
	if self._defenseQuery then
		return self._defenseQuery(routeId)
	end
	return { wallCount = 0, wallHealth = 0, slowTrapCount = 0 }
end

function RouteService.getRouteCost(self: Service, routeId: RouteId): number
	local state = self:getDefenseState(routeId)
	return (RouteConfig.baseTravelCost[routeId] or 0)
		+ state.wallCount * RouteConfig.wallCost
		+ state.slowTrapCount * RouteConfig.slowTrapCost
end

function RouteService.chooseRoamerRoute(self: Service): RouteId
	local leftCost = self:getRouteCost("Left")
	local rightCost = self:getRouteCost("Right")
	if leftCost == rightCost then
		return if self._random:NextNumber() < 0.5 then "Left" else "Right"
	end

	local preferred: RouteId = if leftCost < rightCost then "Left" else "Right"
	return if self._random:NextNumber() <= RouteConfig.roamerPreferredChance
		then preferred
		else otherRoute(preferred)
end

function RouteService.chooseBruteRoute(self: Service): RouteId
	local left = self:getDefenseState("Left")
	local right = self:getDefenseState("Right")
	if left.wallHealth > right.wallHealth then
		return "Left"
	elseif right.wallHealth > left.wallHealth then
		return "Right"
	end

	local selected: RouteId = self._nextBruteTie
	self._nextBruteTie = otherRoute(selected)
	return selected :: RouteId
end

function RouteService.chooseWaveThreeBruteRoutes(self: Service): { RouteId }
	local left = self:getDefenseState("Left")
	local right = self:getDefenseState("Right")
	if left.wallCount > 0 and right.wallCount > 0 then
		return { "Left" :: RouteId, "Right" :: RouteId }
	end
	local first = self:chooseBruteRoute()
	if first == "Left" then
		return { "Left" :: RouteId, "Right" :: RouteId }
	end
	return { "Right" :: RouteId, "Left" :: RouteId }
end

function RouteService.hideReviewMarkers(self: Service)
	for _, child in self._reviewMarkers:GetChildren() do
		if child:IsA("BasePart") then
			child.Transparency = 1
		end
	end
	local breachMarker = self._reviewMarkers:FindFirstChild("FirstBreachMarker")
	local label = if breachMarker then breachMarker:FindFirstChild("BreachLabel") else nil
	if label and label:IsA("BillboardGui") then
		label.Enabled = false
	end
end

function RouteService.showReviewMarkers(self: Service, report: ReviewReport)
	local total = report.LeftLaneEnemyCount + report.RightLaneEnemyCount
	for _, routeId in ipairs({ "Left" :: RouteId, "Right" :: RouteId }) do
		local marker = self._reviewMarkers:FindFirstChild(routeId .. "LaneMarker")
		if marker and marker:IsA("BasePart") then
			local count = if routeId == "Left"
				then report.LeftLaneEnemyCount
				else report.RightLaneEnemyCount
			local ratio = if total > 0 then count / total else 0
			marker.Transparency = math.clamp(0.82 - ratio * 0.45, 0.35, 0.82)
		end
	end

	if report.FirstBreachPadId == "" then
		return
	end
	local pad = self._buildPads:FindFirstChild(report.FirstBreachPadId)
	local marker = self._reviewMarkers:FindFirstChild("FirstBreachMarker")
	if pad and pad:IsA("BasePart") and marker and marker:IsA("BasePart") then
		marker.CFrame = CFrame.new(pad.Position + Vector3.new(0, 3.5, 0))
		marker.Transparency = 0.12
		local label = marker:FindFirstChild("BreachLabel")
		if label and label:IsA("BillboardGui") then
			label.Enabled = true
		end
	end
end

return RouteService
