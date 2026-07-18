--!strict

export type RouteId = "Left" | "Right"
export type RouteDefenseState = {
	wallCount: number,
	wallHealth: number,
	slowTrapCount: number,
}
export type TargetScore = {
	progress: number,
	coreDamage: number,
	spawnSerial: number,
}

local CombatRoutingPolicy = {}

local function otherRoute(routeId: RouteId): RouteId
	return if routeId == "Left" then "Right" else "Left"
end

function CombatRoutingPolicy.RouteCost(
	state: RouteDefenseState,
	baseTravelCost: number,
	wallCost: number,
	slowTrapCost: number
): number
	return math.max(0, baseTravelCost)
		+ math.max(0, state.wallCount) * math.max(0, wallCost)
		+ math.max(0, state.slowTrapCount) * math.max(0, slowTrapCost)
end

function CombatRoutingPolicy.ChooseRoamerRoute(
	leftCost: number,
	rightCost: number,
	randomValue: number,
	preferredChance: number
): RouteId
	local roll = math.clamp(randomValue, 0, 1)
	if leftCost == rightCost then
		return if roll < 0.5 then "Left" else "Right"
	end
	local preferred: RouteId = if leftCost < rightCost then "Left" else "Right"
	return if roll < math.clamp(preferredChance, 0, 1) then preferred else otherRoute(preferred)
end

function CombatRoutingPolicy.ChooseBruteRoute(
	left: RouteDefenseState,
	right: RouteDefenseState,
	nextTie: RouteId
): (RouteId, RouteId)
	if left.wallHealth > right.wallHealth then
		return "Left", nextTie
	elseif right.wallHealth > left.wallHealth then
		return "Right", nextTie
	end
	return nextTie, otherRoute(nextTie)
end

function CombatRoutingPolicy.ChooseWaveThreeBruteRoutes(
	left: RouteDefenseState,
	right: RouteDefenseState,
	nextTie: RouteId
): ({ RouteId }, RouteId)
	if left.wallCount > 0 and right.wallCount > 0 then
		return { "Left", "Right" }, nextTie
	end
	local first: RouteId, followingTie: RouteId =
		CombatRoutingPolicy.ChooseBruteRoute(left, right, nextTie)
	if first == "Left" then
		return { "Left", "Right" }, followingTie
	end
	return { "Right", "Left" }, followingTie
end

function CombatRoutingPolicy.FirstBlockingWallId(
	pathCellKeys: { string },
	pointIndex: number,
	wallIdByCell: { [string]: string },
	maxLookaheadCells: number
): string?
	local startIndex = math.max(1, math.floor(pointIndex))
	local finalIndex =
		math.min(#pathCellKeys, startIndex + math.max(0, math.floor(maxLookaheadCells)))
	for index = startIndex, finalIndex do
		local wallId = wallIdByCell[pathCellKeys[index]]
		if wallId then
			return wallId
		end
	end
	return nil
end

function CombatRoutingPolicy.IsHigherPriorityTarget(
	candidate: TargetScore,
	current: TargetScore?
): boolean
	if not current then
		return true
	end
	if candidate.progress ~= current.progress then
		return candidate.progress > current.progress
	end
	if candidate.coreDamage ~= current.coreDamage then
		return candidate.coreDamage > current.coreDamage
	end
	return candidate.spawnSerial < current.spawnSerial
end

return table.freeze(CombatRoutingPolicy)
