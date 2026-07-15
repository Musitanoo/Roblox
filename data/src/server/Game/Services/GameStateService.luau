--!strict

type GameState = "PREPARATION" | "STARTING" | "DEFENDING" | "VICTORY" | "DEFEAT" | "REVIEW"

local ALLOWED_TRANSITIONS: { [GameState]: { [GameState]: boolean } } = {
	PREPARATION = { STARTING = true },
	STARTING = { DEFENDING = true },
	DEFENDING = { VICTORY = true, DEFEAT = true },
	VICTORY = { REVIEW = true },
	DEFEAT = { REVIEW = true },
	REVIEW = { PREPARATION = true },
}

local GameStateService = {}
GameStateService.__index = GameStateService

export type Service = typeof(setmetatable(
	{} :: {
		_replicaRoot: Folder,
		_stateChanged: RemoteEvent,
		_core: BasePart,
		_phase: GameState,
		_coreMaxHealth: number,
	},
	GameStateService
))

local function updateCoreVisual(core: BasePart, health: number, maxHealth: number)
	local ratio = if maxHealth > 0 then math.clamp(health / maxHealth, 0, 1) else 0
	core.Color = if ratio <= 0.3
		then Color3.fromRGB(255, 70, 70)
		elseif ratio <= 0.6 then Color3.fromRGB(255, 188, 65)
		else Color3.fromRGB(45, 145, 255)

	local label = core:FindFirstChild("Label", true)
	if label and label:IsA("TextLabel") then
		label.Text = string.format("NOYAU • %d PV", math.floor(health + 0.5))
	end
end

function GameStateService.new(
	replicaRoot: Folder,
	stateChanged: RemoteEvent,
	core: BasePart,
	coreMaxHealth: number
): Service
	local self: Service = setmetatable({
		_replicaRoot = replicaRoot,
		_stateChanged = stateChanged,
		_core = core,
		_phase = "PREPARATION" :: GameState,
		_coreMaxHealth = coreMaxHealth,
	}, GameStateService)

	replicaRoot:SetAttribute("Phase", self._phase)
	replicaRoot:SetAttribute("Countdown", 0)
	replicaRoot:SetAttribute("Wave", 0)
	replicaRoot:SetAttribute("TotalWaves", 0)
	replicaRoot:SetAttribute("EnemiesRemaining", 0)
	replicaRoot:SetAttribute("BruteWarning", "")
	replicaRoot:SetAttribute("CoreMaxHealth", coreMaxHealth)
	self:restoreCore()
	return self
end

function GameStateService.getPhase(self: Service): GameState
	return self._phase
end

function GameStateService.setPhase(self: Service, nextPhase: GameState): boolean
	if nextPhase == self._phase then
		return true
	end
	if ALLOWED_TRANSITIONS[self._phase][nextPhase] ~= true then
		return false
	end

	self._phase = nextPhase
	self._replicaRoot:SetAttribute("Phase", nextPhase)
	self._stateChanged:FireAllClients(nextPhase)
	return true
end

function GameStateService.setCountdown(self: Service, secondsRemaining: number)
	self._replicaRoot:SetAttribute("Countdown", math.max(0, math.floor(secondsRemaining)))
end

function GameStateService.setWave(self: Service, wave: number, totalWaves: number)
	self._replicaRoot:SetAttribute("Wave", math.max(0, math.floor(wave)))
	self._replicaRoot:SetAttribute("TotalWaves", math.max(0, math.floor(totalWaves)))
end

function GameStateService.setEnemiesRemaining(self: Service, count: number)
	self._replicaRoot:SetAttribute("EnemiesRemaining", math.max(0, math.floor(count)))
end

function GameStateService.setBruteWarning(self: Service, message: string)
	self._replicaRoot:SetAttribute("BruteWarning", string.sub(message, 1, 80))
end

function GameStateService.restoreCore(self: Service)
	self._core:SetAttribute("MaxHealth", self._coreMaxHealth)
	self._core:SetAttribute("Health", self._coreMaxHealth)
	self._replicaRoot:SetAttribute("CoreHealth", self._coreMaxHealth)
	updateCoreVisual(self._core, self._coreMaxHealth, self._coreMaxHealth)
end

function GameStateService.getCoreHealth(self: Service): number
	local value = self._core:GetAttribute("Health")
	return if typeof(value) == "number" then value else self._coreMaxHealth
end

function GameStateService.damageCore(self: Service, damage: number): number
	local nextHealth = math.max(0, self:getCoreHealth() - math.max(0, damage))
	self._core:SetAttribute("Health", nextHealth)
	self._replicaRoot:SetAttribute("CoreHealth", nextHealth)
	updateCoreVisual(self._core, nextHealth, self._coreMaxHealth)
	return nextHealth
end

function GameStateService.clearTransient(self: Service)
	self:setCountdown(0)
	self:setWave(0, 0)
	self:setEnemiesRemaining(0)
	self:setBruteWarning("")
end

return GameStateService
