--!strict

export type GameState = "PREPARATION" | "STARTING" | "DEFENDING" | "VICTORY" | "DEFEAT" | "REVIEW"
export type Outcome = "VICTORY" | "DEFEAT"
export type DefenseType = "Empty" | "Wall" | "SlowTrap" | "Turret"
export type EnemyType = "Roamer" | "Brute"
export type RouteId = "Left" | "Right"
export type DefenseSnapshot = { [string]: DefenseType }

export type ChallengeWave = {
	id: number,
	roamerCount: number,
	roamerIntervalSeconds: number,
	fixedLeftRoamers: number,
	fixedRightRoamers: number,
	bruteCount: number,
	restSeconds: number,
}

export type ReviewReport = {
	Result: Outcome,
	ChallengeId: string,
	ChallengeDuration: number,
	CoreHealthRemaining: number,
	LeftLaneEnemyCount: number,
	RightLaneEnemyCount: number,
	LeftLaneCoreHits: number,
	RightLaneCoreHits: number,
	FirstBreachTime: number,
	FirstBreachLane: string,
	FirstBreachPadId: string,
	FirstBreachEnemyType: string,
	TotalWallDamageAbsorbed: number,
	TotalTurretDamage: number,
	TotalEnemiesSlowed: number,
	EnemiesReachedCore: number,
}

local DEFENSE_TYPES: { [string]: boolean } = {
	Empty = true,
	Wall = true,
	SlowTrap = true,
	Turret = true,
}

local ENEMY_TYPES: { [string]: boolean } = {
	Roamer = true,
	Brute = true,
}

local ROUTE_IDS: { [string]: boolean } = {
	Left = true,
	Right = true,
}

local GameTypes = {}

function GameTypes.isDefenseType(value: unknown): boolean
	return typeof(value) == "string" and DEFENSE_TYPES[value] == true
end

function GameTypes.isEnemyType(value: unknown): boolean
	return typeof(value) == "string" and ENEMY_TYPES[value] == true
end

function GameTypes.isRouteId(value: unknown): boolean
	return typeof(value) == "string" and ROUTE_IDS[value] == true
end

return table.freeze(GameTypes)
