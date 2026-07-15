--!strict

local costs = {
	Empty = 0,
	Wall = 1,
	SlowTrap = 1,
	Turret = 2,
}

local DefenseConfig = {
	maxBudget = 8,
	interactionDistance = 18,
	requestCooldownSeconds = 0.15,
	costs = table.freeze(costs),
	wall = table.freeze({
		maxHealth = 700,
		blocksLane = true,
	}),
	slowTrap = table.freeze({
		maxHealth = 250,
		slowMultiplier = 0.55,
		effectDurationSeconds = 1.25,
		effectRadius = 10.5,
	}),
	turret = table.freeze({
		maxHealth = 350,
		range = 28,
		damage = 18,
		cooldownSeconds = 0.35,
	}),
}

return table.freeze(DefenseConfig)
