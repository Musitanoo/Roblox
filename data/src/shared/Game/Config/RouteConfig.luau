--!strict

local RouteConfig = {
	routes = table.freeze({ "Left", "Right" }),
	wallCost = 40,
	slowTrapCost = 15,
	roamerPreferredChance = 0.75,
	baseTravelCost = table.freeze({
		Left = 0,
		Right = 0,
	}),
}

return table.freeze(RouteConfig)
