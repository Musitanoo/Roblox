--!strict

type WaveConfig = {
	count: number,
	spawnIntervalSeconds: number,
}

local waves: { WaveConfig } = {
	{
		count = 4,
		spawnIntervalSeconds = 4.5,
	},
	{
		count = 6,
		spawnIntervalSeconds = 4,
	},
	{
		count = 8,
		spawnIntervalSeconds = 3.5,
	},
}

for _, wave in waves do
	table.freeze(wave)
end

local ChallengeConfig = {
	countdownSeconds = 3,
	intermissionSeconds = 10,
	outcomeDisplaySeconds = 2,
	coreMaxHealth = 500,
	coreDamagePerEnemy = 40,
	interactionDistance = 18,
	requestCooldownSeconds = 0.25,
	waves = table.freeze(waves),
}

return table.freeze(ChallengeConfig)
