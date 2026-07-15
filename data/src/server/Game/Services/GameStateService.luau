--!strict

type GameState = "PREPARATION" | "STARTING" | "DEFENDING" | "VICTORY" | "DEFEAT" | "REVIEW"
type Outcome = "VICTORY" | "DEFEAT"

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

local function getHealthColor(ratio: number): Color3
	if ratio <= 0.3 then
		return Color3.fromRGB(230, 65, 65)
	end
	if ratio <= 0.6 then
		return Color3.fromRGB(255, 196, 61)
	end
	return Color3.fromRGB(73, 190, 103)
end

local function updateCoreVisual(core: BasePart, health: number, maxHealth: number)
	local ratio = if maxHealth > 0 then math.clamp(health / maxHealth, 0, 1) else 0
	local billboard = core:FindFirstChild("CoreBillboard")
	if billboard and billboard:IsA("BillboardGui") then
		local fill = billboard:FindFirstChild("Fill", true)
		if fill and fill:IsA("Frame") then
			fill.Size = UDim2.fromScale(ratio, 1)
			fill.BackgroundColor3 = getHealthColor(ratio)
		end
	end

	local light = core:FindFirstChild("CoreLight")
	if light and light:IsA("PointLight") then
		light.Color = if ratio <= 0.3 then Color3.fromRGB(255, 88, 88) else core.Color
		light.Brightness = 1.5 + ratio * 2.5
	end
end

export type Service = typeof(setmetatable(
	{} :: {
		_replicaRoot: Folder,
		_core: BasePart,
		_phase: GameState,
		_coreMaxHealth: number,
	},
	GameStateService
))

function GameStateService.new(replicaRoot: Folder, core: BasePart, coreMaxHealth: number): Service
	local self: Service = setmetatable({
		_replicaRoot = replicaRoot,
		_core = core,
		_phase = "PREPARATION" :: GameState,
		_coreMaxHealth = coreMaxHealth,
	}, GameStateService)

	replicaRoot:SetAttribute("Phase", self._phase)
	replicaRoot:SetAttribute("Countdown", 0)
	replicaRoot:SetAttribute("Wave", 0)
	replicaRoot:SetAttribute("TotalWaves", 0)
	replicaRoot:SetAttribute("Outcome", "")
	replicaRoot:SetAttribute("FirstDestroyed", "Aucune")
	replicaRoot:SetAttribute("ReachedCore", 0)
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

	local allowedFromCurrent = ALLOWED_TRANSITIONS[self._phase]
	if allowedFromCurrent[nextPhase] ~= true then
		return false
	end

	self._phase = nextPhase
	self._replicaRoot:SetAttribute("Phase", nextPhase)
	return true
end

function GameStateService.setCountdown(self: Service, secondsRemaining: number)
	self._replicaRoot:SetAttribute("Countdown", math.max(0, math.floor(secondsRemaining)))
end

function GameStateService.setWave(self: Service, wave: number, totalWaves: number)
	self._replicaRoot:SetAttribute("Wave", math.max(0, math.floor(wave)))
	self._replicaRoot:SetAttribute("TotalWaves", math.max(0, math.floor(totalWaves)))
end

function GameStateService.restoreCore(self: Service)
	self._core:SetAttribute("MaxHealth", self._coreMaxHealth)
	self._core:SetAttribute("Health", self._coreMaxHealth)
	self._replicaRoot:SetAttribute("CoreHealth", self._coreMaxHealth)
	updateCoreVisual(self._core, self._coreMaxHealth, self._coreMaxHealth)
end

function GameStateService.damageCore(self: Service, damage: number): number
	local currentHealth = self._core:GetAttribute("Health")
	local health = if typeof(currentHealth) == "number" then currentHealth else self._coreMaxHealth
	local nextHealth = math.max(0, health - math.max(0, damage))
	self._core:SetAttribute("Health", nextHealth)
	self._replicaRoot:SetAttribute("CoreHealth", nextHealth)
	updateCoreVisual(self._core, nextHealth, self._coreMaxHealth)
	return nextHealth
end

function GameStateService.setReachedCore(self: Service, count: number)
	self._replicaRoot:SetAttribute("ReachedCore", math.max(0, math.floor(count)))
end

function GameStateService.setReview(
	self: Service,
	outcome: Outcome,
	firstDestroyed: string,
	reachedCore: number
)
	self._replicaRoot:SetAttribute("Outcome", outcome)
	self._replicaRoot:SetAttribute("FirstDestroyed", firstDestroyed)
	self:setReachedCore(reachedCore)
end

function GameStateService.clearReview(self: Service)
	self._replicaRoot:SetAttribute("Outcome", "")
	self._replicaRoot:SetAttribute("FirstDestroyed", "Aucune")
	self._replicaRoot:SetAttribute("ReachedCore", 0)
	self:setCountdown(0)
	self:setWave(0, 0)
end

return GameStateService
