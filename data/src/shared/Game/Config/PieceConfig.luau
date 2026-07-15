--!strict

local PieceConfig = {
	Wall = table.freeze({
		footprintWidth = 1,
		footprintDepth = 2,
		canRotate = true,
		structureCost = 2,
		powerCost = 0,
		maxHealth = 700,
		blocksPath = true,
		roamerCost = 90,
		bruteCost = 35,
		queryHeight = 5.8,
	}),
	SlowTrap = table.freeze({
		footprintWidth = 1,
		footprintDepth = 1,
		canRotate = false,
		structureCost = 1,
		powerCost = 1,
		maxHealth = 250,
		blocksPath = false,
		roamerCost = 20,
		bruteCost = 15,
		queryHeight = 0.7,
	}),
	Turret = table.freeze({
		footprintWidth = 1,
		footprintDepth = 1,
		canRotate = true,
		structureCost = 3,
		powerCost = 2,
		maxHealth = 350,
		blocksPath = true,
		roamerCost = 55,
		bruteCost = 30,
		queryHeight = 5.8,
	}),
}

return table.freeze(PieceConfig)
