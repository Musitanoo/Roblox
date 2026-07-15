--!strict

local EnemyConfig = {
	maxHealth = 100,
	moveSpeed = 5,
	wallDetectionRange = 10,
	wallAttackDamage = 30,
	wallAttackCooldownSeconds = 1,
	maxActiveEnemies = 24,
}

return table.freeze(EnemyConfig)
