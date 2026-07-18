--!strict

local RouteConfig = {
	wallCost = 40,
	slowTrapCost = 15,
	gridBaseStepCost = 10,
	roamerPreferredChance = 0.75,
	baseTravelCost = table.freeze({
		Left = 0,
		Right = 0,
	}),
}

return table.freeze(RouteConfig)
