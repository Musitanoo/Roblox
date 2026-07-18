--!strict

local ServerScriptService = game:GetService("ServerScriptService")

type RouteId = "Left" | "Right"
type RouteDefenseState = {
	wallCount: number,
	wallHealth: number,
	slowTrapCount: number,
}
type TargetScore = {
	progress: number,
	coreDamage: number,
	spawnSerial: number,
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
	FirstBlockingWallId: ({ string }, number, { [string]: string }, number) -> string?,
	IsHigherPriorityTarget: (TargetScore, TargetScore?) -> boolean,
}

local serverRoot = ServerScriptService:WaitForChild("Server")
local gameFolder = serverRoot:WaitForChild("Game")
local CombatRoutingPolicy =
	require(gameFolder:WaitForChild("CombatRoutingPolicy") :: ModuleScript) :: CombatRoutingPolicyModule

local CombatRoutingPolicySpec = {}

local function expect(condition: boolean, message: string)
	if not condition then
		error(message, 2)
	end
end

local EMPTY: RouteDefenseState = {
	wallCount = 0,
	wallHealth = 0,
	slowTrapCount = 0,
}

function CombatRoutingPolicySpec.run()
	local fortified: RouteDefenseState = {
		wallCount = 2,
		wallHealth = 900,
		slowTrapCount = 3,
	}
	expect(
		CombatRoutingPolicy.RouteCost(fortified, 5, 40, 15) == 130,
		"route cost must be base + 40 per live wall + 15 per live slow trap"
	)

	expect(
		CombatRoutingPolicy.ChooseRoamerRoute(40, 80, 0.74, 0.75) == "Left",
		"Roamer must prefer the cheaper lane inside the 75 percent branch"
	)
	expect(
		CombatRoutingPolicy.ChooseRoamerRoute(40, 80, 0.76, 0.75) == "Right",
		"Roamer must take the other lane outside the preferred branch"
	)
	expect(
		CombatRoutingPolicy.ChooseRoamerRoute(40, 80, 0.75, 0.75) == "Right",
		"the exact 75 percent boundary must start the other-lane branch"
	)
	expect(
		CombatRoutingPolicy.ChooseRoamerRoute(40, 40, 0.5, 0.75) == "Right",
		"equal Roamer costs must use a deterministic interpretation of the supplied roll"
	)

	local selected: RouteId
	local nextTie: RouteId
	selected, nextTie = CombatRoutingPolicy.ChooseBruteRoute(fortified, EMPTY, "Left")
	expect(selected == "Left" and nextTie == "Left", "Brute must choose higher live wall health")
	selected, nextTie = CombatRoutingPolicy.ChooseBruteRoute(EMPTY, EMPTY, "Left")
	expect(selected == "Left" and nextTie == "Right", "first Brute tie must choose Left")
	selected, nextTie = CombatRoutingPolicy.ChooseBruteRoute(EMPTY, EMPTY, nextTie)
	expect(selected == "Right" and nextTie == "Left", "Brute ties must alternate")

	local rightFortified: RouteDefenseState = {
		wallCount = 1,
		wallHealth = 700,
		slowTrapCount = 0,
	}
	local routes: { RouteId }
	routes, nextTie =
		CombatRoutingPolicy.ChooseWaveThreeBruteRoutes(fortified, rightFortified, "Right")
	expect(
		routes[1] == "Left" and routes[2] == "Right" and nextTie == "Right",
		"wave three must assign one Brute per lane when both contain live walls"
	)
	routes, nextTie = CombatRoutingPolicy.ChooseWaveThreeBruteRoutes(EMPTY, rightFortified, "Left")
	expect(
		routes[1] == "Right" and routes[2] == "Left",
		"otherwise wave three must start on the lane with more live wall health"
	)

	local path = { "2:12", "2:11", "2:10", "3:10" }
	local wallIds = {
		["9:9"] = "off-route",
		["2:11"] = "first-on-route",
		["2:10"] = "second-on-route",
	}
	expect(
		CombatRoutingPolicy.FirstBlockingWallId(path, 1, wallIds, 3) == "first-on-route",
		"the first remaining wall on the enemy path must win over global proximity"
	)
	expect(
		CombatRoutingPolicy.FirstBlockingWallId(path, 3, wallIds, 3) == "second-on-route",
		"walls behind the enemy point index must be ignored"
	)
	wallIds["2:11"] = nil
	expect(
		CombatRoutingPolicy.FirstBlockingWallId(path, 1, wallIds, 3) == "second-on-route",
		"a destroyed wall removed from live occupancy must not remain a phantom blocker"
	)
	expect(
		CombatRoutingPolicy.FirstBlockingWallId(path, 1, wallIds, 0) == nil,
		"lookahead must remain bounded"
	)

	local current: TargetScore = { progress = 0.6, coreDamage = 120, spawnSerial = 4 }
	expect(
		CombatRoutingPolicy.IsHigherPriorityTarget(
			{ progress = 0.7, coreDamage = 40, spawnSerial = 8 },
			current
		),
		"route progress must be the primary turret priority"
	)
	expect(
		CombatRoutingPolicy.IsHigherPriorityTarget(
			{ progress = 0.6, coreDamage = 140, spawnSerial = 8 },
			current
		),
		"core threat must break equal-progress ties"
	)
	expect(
		CombatRoutingPolicy.IsHigherPriorityTarget(
			{ progress = 0.6, coreDamage = 120, spawnSerial = 2 },
			current
		),
		"older spawn serial must provide the final deterministic tie-break"
	)
end

return table.freeze(CombatRoutingPolicySpec)
