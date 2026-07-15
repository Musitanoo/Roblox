--!strict

export type GameState = "PREPARATION" | "STARTING" | "DEFENDING" | "VICTORY" | "DEFEAT" | "REVIEW"

export type DefenseType = "Empty" | "Wall" | "Turret"
export type StartAction = "Start" | "ReturnToPreparation"
export type Outcome = "VICTORY" | "DEFEAT"

export type WaveConfig = {
	count: number,
	spawnIntervalSeconds: number,
}

export type DefenseSnapshot = { [string]: DefenseType }

local DEFENSE_TYPES: { [string]: boolean } = {
	Empty = true,
	Wall = true,
	Turret = true,
}

local START_ACTIONS: { [string]: boolean } = {
	Start = true,
	ReturnToPreparation = true,
}

local GameTypes = {}

function GameTypes.isDefenseType(value: unknown): boolean
	return typeof(value) == "string" and DEFENSE_TYPES[value] == true
end

function GameTypes.isStartAction(value: unknown): boolean
	return typeof(value) == "string" and START_ACTIONS[value] == true
end

return table.freeze(GameTypes)
