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
type ReviewReport = {
	LeftLaneEnemyCount: number,
	RightLaneEnemyCount: number,
	FirstBreachLane: string,
	FirstBreachPadId: string,
}
type RouteSolverModule = {
	Solve: (BuildPlan, RouteId, EnemyType) -> ({ { x: number, z: number } }?, number),
}
type GridMathModule = {
	CellToWorld: (CFrame, number, number) -> Vector3,
}
type RouteConfigType = { roamerPreferredChance: number }
type PlanQuery = () -> BuildPlan

local sharedGame = ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Game")
local config = sharedGame:WaitForChild("Config")
local GridMath = require(sharedGame:WaitForChild("GridMath") :: ModuleScript) :: GridMathModule
local RouteConfig = require(config:WaitForChild("RouteConfig") :: ModuleScript) :: RouteConfigType
local RouteSolver =
	require(sharedGame:WaitForChild("RouteSolver") :: ModuleScript) :: RouteSolverModule

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
	},
	GridRouteService
))

local function otherRoute(routeId: RouteId): RouteId
	return if routeId == "Left" then "Right" :: RouteId else "Left" :: RouteId
end

function GridRouteService.new(prototype: Folder, random: Random?): Service
	local enemySpawns = prototype:FindFirstChild("EnemySpawns")
	local reviewMarkers = prototype:FindFirstChild("ReviewMarkers")
	local surface = prototype:FindFirstChild("BuildSurface")
	assert(enemySpawns and enemySpawns:IsA("Folder"), "Prototype.EnemySpawns is required")
	assert(reviewMarkers and reviewMarkers:IsA("Folder"), "Prototype.ReviewMarkers is required")
	assert(surface and surface:IsA("BasePart"), "Prototype.BuildSurface is required")
	local leftSpawn = enemySpawns:FindFirstChild("LeftSpawn")
	local rightSpawn = enemySpawns:FindFirstChild("RightSpawn")
	assert(leftSpawn and leftSpawn:IsA("BasePart"), "LeftSpawn is required")
	assert(rightSpawn and rightSpawn:IsA("BasePart"), "RightSpawn is required")
	local self: Service = setmetatable({
		_spawns = { Left = leftSpawn, Right = rightSpawn },
		_surface = surface,
		_reviewMarkers = reviewMarkers,
		_random = random or Random.new(),
		_nextBruteTie = "Left" :: RouteId,
		_planQuery = nil,
	}, GridRouteService)
	self:hideReviewMarkers()
	return self
end

function GridRouteService.setPlanQuery(self: Service, query: PlanQuery)
	self._planQuery = query
end

function GridRouteService._getPlan(self: Service): BuildPlan
	assert(self._planQuery, "GridRouteService plan query is required")
	return self._planQuery()
end

function GridRouteService.getSpawn(self: Service, routeId: RouteId): BasePart
	return self._spawns[routeId]
end

function GridRouteService.getPath(
	self: Service,
	routeId: RouteId,
	enemyType: EnemyType
): { Vector3 }
	local cells = RouteSolver.Solve(self:_getPlan(), routeId, enemyType)
	local points: { Vector3 } = {}
	if cells then
		for _, cell in cells do
			table.insert(points, GridMath.CellToWorld(self._surface.CFrame, cell.x, cell.z))
		end
	end
	return points
end

function GridRouteService.getRouteCost(
	self: Service,
	routeId: RouteId,
	enemyType: EnemyType
): number
	local _, cost = RouteSolver.Solve(self:_getPlan(), routeId, enemyType)
	return cost
end

function GridRouteService.chooseRoamerRoute(self: Service): RouteId
	local leftCost = self:getRouteCost("Left", "Roamer")
	local rightCost = self:getRouteCost("Right", "Roamer")
	if leftCost == rightCost then
		return if self._random:NextNumber() < 0.5 then "Left" else "Right"
	end
	local preferred: RouteId = if leftCost < rightCost then "Left" else "Right"
	return if self._random:NextNumber() <= RouteConfig.roamerPreferredChance
		then preferred
		else otherRoute(preferred)
end

function GridRouteService.chooseBruteRoute(self: Service): RouteId
	local leftCost = self:getRouteCost("Left", "Brute")
	local rightCost = self:getRouteCost("Right", "Brute")
	if leftCost > rightCost then
		return "Left"
	elseif rightCost > leftCost then
		return "Right"
	end
	local selected: RouteId = self._nextBruteTie :: RouteId
	self._nextBruteTie = otherRoute(selected)
	return selected
end

function GridRouteService.chooseWaveThreeBruteRoutes(self: Service): { RouteId }
	local first: RouteId = self:chooseBruteRoute()
	return { first, otherRoute(first) }
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
		local position = GridMath.CellToWorld(self._surface.CFrame, piece.cellX, piece.cellZ)
		marker.CFrame = CFrame.new(position + Vector3.new(0, 3.5, 0))
		marker.Transparency = 0.12
		local label = marker:FindFirstChild("BreachLabel")
		if label and label:IsA("BillboardGui") then
			label.Enabled = true
		end
	end
end

return GridRouteService
