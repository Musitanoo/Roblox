--!strict

local ReplicatedStorage = game:GetService("ReplicatedStorage")

type RouteId = "Left" | "Right"
type EnemyType = "Roamer" | "Brute"
type PieceType = "Wall" | "SlowTrap" | "Turret"
type BuildPieceData = {
	id: string,
	pieceType: PieceType,
	cellX: number,
	cellZ: number,
	rotation: number,
}
type BuildPlan = { schemaVersion: number, revision: number, pieces: { [string]: BuildPieceData } }
type Cell = { x: number, z: number }
type RouteDefenseState = {
	wallCount: number,
	wallHealth: number,
	slowTrapCount: number,
}
type ReviewReport = {
	LeftLaneEnemyCount: number,
	RightLaneEnemyCount: number,
	FirstBreachLane: string,
	FirstBreachPadId: string,
}
type RouteSolverModule = {
	Solve: (BuildPlan, RouteId, EnemyType) -> ({ Cell }?, number),
}
type GridMathModule = {
	CellToWorld: (CFrame, number, number) -> Vector3,
	CellKey: (number, number) -> string,
	GetPieceWorldCFrame: (CFrame, BuildPieceData) -> CFrame,
}
type GridConfig = { buildSurfaceName: string }
type RouteConfigType = {
	wallCost: number,
	slowTrapCost: number,
	roamerPreferredChance: number,
	baseTravelCost: { [string]: number },
}
type CombatRoutingPolicyModule = {
	RouteCost: (RouteDefenseState, number, number, number) -> number,
	ChooseRoamerRoute: (number, number, number, number) -> RouteId,
	ChooseBruteRoute: (RouteDefenseState, RouteDefenseState, RouteId) -> (RouteId, RouteId),
	ChooseWaveThreeBruteRoutes: (
		RouteDefenseState,
		RouteDefenseState,
		RouteId
	) -> ({ RouteId }, RouteId),
}
type PlanQuery = () -> BuildPlan
type DefenseQuery = (RouteId) -> RouteDefenseState

local sharedGame = ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Game")
local config = sharedGame:WaitForChild("Config")
local BuildGridConfig =
	require(config:WaitForChild("BuildGridConfig") :: ModuleScript) :: GridConfig
local GridMath = require(sharedGame:WaitForChild("GridMath") :: ModuleScript) :: GridMathModule
local RouteConfig = require(config:WaitForChild("RouteConfig") :: ModuleScript) :: RouteConfigType
local RouteSolver =
	require(sharedGame:WaitForChild("RouteSolver") :: ModuleScript) :: RouteSolverModule
local servicesFolder = script.Parent
assert(
	servicesFolder and servicesFolder:IsA("Folder"),
	"GridRouteService must be under Game.Services"
)
local gameFolder = servicesFolder.Parent
assert(gameFolder and gameFolder:IsA("Folder"), "Game.Services must be under Game")
local CombatRoutingPolicy =
	require(gameFolder:WaitForChild("CombatRoutingPolicy") :: ModuleScript) :: CombatRoutingPolicyModule

local GridRouteService = {}
GridRouteService.__index = GridRouteService

export type Service = typeof(setmetatable(
	{} :: {
		_spawns: { Left: BasePart, Right: BasePart },
		_surface: BasePart,
		_reviewMarkers: Folder,
		_random: Random,
		_nextBruteTie: RouteId,
		_planQuery: PlanQuery?,
		_livePlanQuery: PlanQuery?,
		_defenseQuery: DefenseQuery?,
	},
	GridRouteService
))

function GridRouteService.new(prototype: Folder, random: Random?): Service
	local enemySpawns = prototype:FindFirstChild("EnemySpawns")
	local reviewMarkers = prototype:FindFirstChild("ReviewMarkers")
	local surface = prototype:FindFirstChild(BuildGridConfig.buildSurfaceName)
	assert(enemySpawns and enemySpawns:IsA("Folder"), "Prototype.EnemySpawns is required")
	assert(reviewMarkers and reviewMarkers:IsA("Folder"), "Prototype.ReviewMarkers is required")
	assert(
		surface and surface:IsA("BasePart"),
		"Prototype." .. BuildGridConfig.buildSurfaceName .. " is required"
	)
	local leftSpawn = enemySpawns:FindFirstChild("LeftSpawn")
	local rightSpawn = enemySpawns:FindFirstChild("RightSpawn")
	assert(leftSpawn and leftSpawn:IsA("BasePart"), "LeftSpawn is required")
	assert(rightSpawn and rightSpawn:IsA("BasePart"), "RightSpawn is required")
	for _, markerName in ipairs({ "LeftLaneMarker", "RightLaneMarker", "FirstBreachMarker" }) do
		local marker = reviewMarkers:FindFirstChild(markerName)
		assert(marker and marker:IsA("BasePart"), "ReviewMarkers." .. markerName .. " is required")
	end
	local firstBreachMarker = reviewMarkers:FindFirstChild("FirstBreachMarker")
	assert(
		firstBreachMarker and firstBreachMarker:IsA("BasePart"),
		"ReviewMarkers.FirstBreachMarker is required"
	)
	local breachLabel = firstBreachMarker:FindFirstChild("BreachLabel")
	assert(
		breachLabel and breachLabel:IsA("BillboardGui"),
		"FirstBreachMarker.BreachLabel is required"
	)
	local self: Service = setmetatable({
		_spawns = { Left = leftSpawn, Right = rightSpawn },
		_surface = surface,
		_reviewMarkers = reviewMarkers,
		_random = random or Random.new(),
		_nextBruteTie = "Left" :: RouteId,
		_planQuery = nil,
		_livePlanQuery = nil,
		_defenseQuery = nil,
	}, GridRouteService)
	self:hideReviewMarkers()
	return self
end

function GridRouteService.setPlanQuery(self: Service, query: PlanQuery)
	self._planQuery = query
end

function GridRouteService.setLivePlanQuery(self: Service, query: PlanQuery)
	self._livePlanQuery = query
end

function GridRouteService.setDefenseQuery(self: Service, query: DefenseQuery)
	self._defenseQuery = query
end

function GridRouteService._getPlan(self: Service): BuildPlan
	assert(self._planQuery, "GridRouteService plan query is required")
	return self._planQuery()
end

function GridRouteService._getRoutingPlan(self: Service): BuildPlan
	assert(self._livePlanQuery, "GridRouteService live plan query is required")
	return self._livePlanQuery()
end

function GridRouteService._getDefenseState(self: Service, routeId: RouteId): RouteDefenseState
	assert(self._defenseQuery, "GridRouteService defense query is required")
	return self._defenseQuery(routeId)
end

function GridRouteService.getSpawn(self: Service, routeId: RouteId): BasePart
	return self._spawns[routeId]
end

function GridRouteService.getPath(
	self: Service,
	routeId: RouteId,
	enemyType: EnemyType
): ({ Vector3 }, { string })
	local cells = RouteSolver.Solve(self:_getRoutingPlan(), routeId, enemyType)
	local points: { Vector3 } = {}
	local cellKeys: { string } = {}
	if cells then
		for _, cell in cells do
			table.insert(points, GridMath.CellToWorld(self._surface.CFrame, cell.x, cell.z))
			table.insert(cellKeys, GridMath.CellKey(cell.x, cell.z))
		end
	end
	return points, cellKeys
end

function GridRouteService.getRouteCost(self: Service, routeId: RouteId): number
	return CombatRoutingPolicy.RouteCost(
		self:_getDefenseState(routeId),
		RouteConfig.baseTravelCost[routeId] or 0,
		RouteConfig.wallCost,
		RouteConfig.slowTrapCost
	)
end

function GridRouteService.chooseRoamerRoute(self: Service): RouteId
	return CombatRoutingPolicy.ChooseRoamerRoute(
		self:getRouteCost("Left"),
		self:getRouteCost("Right"),
		self._random:NextNumber(),
		RouteConfig.roamerPreferredChance
	)
end

function GridRouteService.chooseBruteRoute(self: Service): RouteId
	local selected: RouteId
	selected, self._nextBruteTie = CombatRoutingPolicy.ChooseBruteRoute(
		self:_getDefenseState("Left"),
		self:_getDefenseState("Right"),
		self._nextBruteTie
	)
	return selected
end

function GridRouteService.chooseWaveThreeBruteRoutes(self: Service): { RouteId }
	local routes: { RouteId }
	routes, self._nextBruteTie = CombatRoutingPolicy.ChooseWaveThreeBruteRoutes(
		self:_getDefenseState("Left"),
		self:_getDefenseState("Right"),
		self._nextBruteTie
	)
	return routes
end

function GridRouteService.hideReviewMarkers(self: Service)
	for _, child in self._reviewMarkers:GetChildren() do
		if child:IsA("BasePart") then
			child.Transparency = 1
		end
	end
	local marker = self._reviewMarkers:FindFirstChild("FirstBreachMarker")
	local label = if marker then marker:FindFirstChild("BreachLabel") else nil
	if label and label:IsA("BillboardGui") then
		label.Enabled = false
	end
end

function GridRouteService.showReviewMarkers(self: Service, report: ReviewReport)
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
	local piece = self:_getPlan().pieces[report.FirstBreachPadId]
	local marker = self._reviewMarkers:FindFirstChild("FirstBreachMarker")
	if piece and marker and marker:IsA("BasePart") then
		local position = GridMath.GetPieceWorldCFrame(self._surface.CFrame, piece).Position
		marker.CFrame = CFrame.new(position + Vector3.new(0, 3.5, 0))
		marker.Transparency = 0.12
		local label = marker:FindFirstChild("BreachLabel")
		if label and label:IsA("BillboardGui") then
			label.Enabled = true
		end
	end
end

return GridRouteService
