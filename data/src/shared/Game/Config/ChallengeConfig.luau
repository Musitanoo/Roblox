--!strict

type ChallengeWave = {
	id: number,
	roamerCount: number,
	roamerIntervalSeconds: number,
	fixedLeftRoamers: number,
	fixedRightRoamers: number,
	bruteCount: number,
	restSeconds: number,
}

local waves: { ChallengeWave } = {
	{
		id = 1,
		roamerCount = 6,
		roamerIntervalSeconds = 0.9,
		fixedLeftRoamers = 3,
		fixedRightRoamers = 3,
		bruteCount = 0,
		restSeconds = 8,
	},
	{
		id = 2,
		roamerCount = 8,
		roamerIntervalSeconds = 14,
		fixedLeftRoamers = 0,
		fixedRightRoamers = 0,
		bruteCount = 1,
		restSeconds = 10,
	},
	{
		id = 3,
		roamerCount = 10,
		roamerIntervalSeconds = 11.5,
		fixedLeftRoamers = 0,
		fixedRightRoamers = 0,
		bruteCount = 2,
		restSeconds = 0,
	},
}

for _, wave in waves do
	table.freeze(wave)
end

local ChallengeConfig = {
	challengeId = "Challenge2_FirstBreach",
	countdownSeconds = 3,
	bruteWarningSeconds = 6,
	outcomeDisplaySeconds = 1.5,
	coreMaxHealth = 1000,
	interactionDistance = 18,
	requestCooldownSeconds = 0.25,
	estimatedDurationMinimumSeconds = 240,
	estimatedDurationMaximumSeconds = 300,
	waves = table.freeze(waves),
}

return table.freeze(ChallengeConfig)
