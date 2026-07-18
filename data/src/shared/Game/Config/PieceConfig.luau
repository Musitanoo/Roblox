--!strict

local PieceConfig = {
	Wall = table.freeze({
		footprintWidth = 1,
		footprintDepth = 2,
		canRotate = true,
		structureCost = 2,
		powerCost = 0,
		maxHealth = 700,
		queryHeight = 5.8,
	}),
	SlowTrap = table.freeze({
		footprintWidth = 1,
		footprintDepth = 1,
		canRotate = false,
		structureCost = 1,
		powerCost = 1,
		maxHealth = 250,
		queryHeight = 0.7,
	}),
	Turret = table.freeze({
		footprintWidth = 1,
		footprintDepth = 1,
		canRotate = true,
		structureCost = 3,
		powerCost = 2,
		maxHealth = 350,
		queryHeight = 5.8,
	}),
}

return table.freeze(PieceConfig)
