--!strict

local DefenseConfig = {
	slowTrap = table.freeze({
		slowMultiplier = 0.55,
		effectDurationSeconds = 1.25,
		effectRadius = 10.5,
	}),
	turret = table.freeze({
		range = 28,
		damage = 18,
		cooldownSeconds = 0.35,
	}),
}

return table.freeze(DefenseConfig)
