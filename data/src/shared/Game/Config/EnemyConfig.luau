--!strict

local EnemyConfig = {
	maxActiveEnemies = 24,
	wallDetectionRange = 10.5,
	arrivalDistance = 0.35,
	roamer = table.freeze({
		maxHealth = 100,
		moveSpeed = 8,
		coreDamage = 40,
		structureDPS = 20,
	}),
	brute = table.freeze({
		maxHealth = 450,
		moveSpeed = 4.5,
		coreDamage = 120,
		structureDPS = 85,
	}),
}

return table.freeze(EnemyConfig)
