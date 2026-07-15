--!strict

local DefenseConfig = {
	interactionDistance = 18,
	requestCooldownSeconds = 0.15,
	wall = table.freeze({
		maxHealth = 360,
	}),
	turret = table.freeze({
		range = 20,
		damage = 12,
		cooldownSeconds = 0.6,
	}),
}

return table.freeze(DefenseConfig)
