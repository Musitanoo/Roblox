--!strict

type Outcome = "VICTORY" | "DEFEAT"
type RouteId = "Left" | "Right"
type EnemyType = "Roamer" | "Brute"
type ReviewReport = {
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
type RouteCounts = { Left: number, Right: number }

local CombatStatsService = {}
CombatStatsService.__index = CombatStatsService

export type Service = typeof(setmetatable(
	{} :: {
		_replicaRoot: Folder,
		_challengeId: string,
		_startedAt: number,
		_running: boolean,
		_laneEnemyCount: RouteCounts,
		_laneCoreHits: RouteCounts,
		_firstBreachTime: number,
		_firstBreachLane: string,
		_firstBreachPadId: string,
		_firstBreachEnemyType: string,
		_totalWallDamageAbsorbed: number,
		_totalTurretDamage: number,
		_totalEnemiesSlowed: number,
		_bruteWallsDestroyed: number,
	},
	CombatStatsService
))

local REPORT_DEFAULTS: { [string]: string | number | boolean } = {
	ReportReady = false,
	Result = "",
	ChallengeId = "",
	ChallengeDuration = 0,
	CoreHealthRemaining = 0,
	LeftLaneEnemyCount = 0,
	RightLaneEnemyCount = 0,
	LeftLaneCoreHits = 0,
	RightLaneCoreHits = 0,
	FirstBreachTime = -1,
	FirstBreachLane = "",
	FirstBreachPadId = "",
	FirstBreachEnemyType = "",
	TotalWallDamageAbsorbed = 0,
	TotalTurretDamage = 0,
	TotalEnemiesSlowed = 0,
	EnemiesReachedCore = 0,
	BruteWallsDestroyed = 0,
	LastWallDestroyedPadId = "",
	LastWallDestroyedEnemyType = "",
}

local function rounded(value: number): number
	return math.floor(value * 10 + 0.5) / 10
end

function CombatStatsService.new(replicaRoot: Folder): Service
	local self: Service = setmetatable({
		_replicaRoot = replicaRoot,
		_challengeId = "",
		_startedAt = 0,
		_running = false,
		_laneEnemyCount = { Left = 0, Right = 0 },
		_laneCoreHits = { Left = 0, Right = 0 },
		_firstBreachTime = -1,
		_firstBreachLane = "",
		_firstBreachPadId = "",
		_firstBreachEnemyType = "",
		_totalWallDamageAbsorbed = 0,
		_totalTurretDamage = 0,
		_totalEnemiesSlowed = 0,
		_bruteWallsDestroyed = 0,
	}, CombatStatsService)
	self:clear()
	return self
end

function CombatStatsService.clear(self: Service)
	self._running = false
	for name, value in REPORT_DEFAULTS do
		self._replicaRoot:SetAttribute(name, value)
	end
end

function CombatStatsService.begin(self: Service, challengeId: string)
	self:clear()
	self._challengeId = challengeId
	self._startedAt = os.clock()
	self._running = true
	self._laneEnemyCount.Left = 0
	self._laneEnemyCount.Right = 0
	self._laneCoreHits.Left = 0
	self._laneCoreHits.Right = 0
	self._firstBreachTime = -1
	self._firstBreachLane = ""
	self._firstBreachPadId = ""
	self._firstBreachEnemyType = ""
	self._totalWallDamageAbsorbed = 0
	self._totalTurretDamage = 0
	self._totalEnemiesSlowed = 0
	self._bruteWallsDestroyed = 0
end

function CombatStatsService.recordEnemySpawn(self: Service, routeId: RouteId)
	if self._running then
		self._laneEnemyCount[routeId] += 1
	end
end

function CombatStatsService.recordCoreHit(self: Service, routeId: RouteId)
	if self._running then
		self._laneCoreHits[routeId] += 1
	end
end

function CombatStatsService.recordWallDamage(self: Service, amount: number)
	if self._running then
		self._totalWallDamageAbsorbed += math.max(0, amount)
	end
end

function CombatStatsService.recordTurretDamage(self: Service, amount: number)
	if self._running then
		self._totalTurretDamage += math.max(0, amount)
	end
end

function CombatStatsService.recordEnemiesSlowed(self: Service, count: number)
	if self._running then
		self._totalEnemiesSlowed += math.max(0, math.floor(count))
	end
end

function CombatStatsService.recordFirstBreach(
	self: Service,
	routeId: RouteId,
	padId: string,
	enemyType: EnemyType
): boolean
	if not self._running or self._firstBreachTime >= 0 then
		return false
	end

	self._firstBreachTime = math.max(0, os.clock() - self._startedAt)
	self._firstBreachLane = routeId
	self._firstBreachPadId = string.sub(padId, 1, 20)
	self._firstBreachEnemyType = enemyType
	return true
end

function CombatStatsService.recordWallDestroyed(self: Service, padId: string, enemyType: EnemyType)
	if not self._running then
		return
	end
	self._replicaRoot:SetAttribute("LastWallDestroyedPadId", string.sub(padId, 1, 20))
	self._replicaRoot:SetAttribute("LastWallDestroyedEnemyType", enemyType)
	if enemyType == "Brute" then
		self._bruteWallsDestroyed += 1
		self._replicaRoot:SetAttribute("BruteWallsDestroyed", self._bruteWallsDestroyed)
	end
end

function CombatStatsService.finish(
	self: Service,
	outcome: Outcome,
	coreHealthRemaining: number
): ReviewReport
	self._running = false
	local report: ReviewReport = {
		Result = outcome,
		ChallengeId = self._challengeId,
		ChallengeDuration = rounded(math.max(0, os.clock() - self._startedAt)),
		CoreHealthRemaining = rounded(math.max(0, coreHealthRemaining)),
		LeftLaneEnemyCount = self._laneEnemyCount.Left,
		RightLaneEnemyCount = self._laneEnemyCount.Right,
		LeftLaneCoreHits = self._laneCoreHits.Left,
		RightLaneCoreHits = self._laneCoreHits.Right,
		FirstBreachTime = rounded(self._firstBreachTime),
		FirstBreachLane = self._firstBreachLane,
		FirstBreachPadId = self._firstBreachPadId,
		FirstBreachEnemyType = self._firstBreachEnemyType,
		TotalWallDamageAbsorbed = rounded(self._totalWallDamageAbsorbed),
		TotalTurretDamage = rounded(self._totalTurretDamage),
		TotalEnemiesSlowed = self._totalEnemiesSlowed,
		EnemiesReachedCore = self._laneCoreHits.Left + self._laneCoreHits.Right,
	}
	self._replicaRoot:SetAttribute("Result", report.Result)
	self._replicaRoot:SetAttribute("ChallengeId", report.ChallengeId)
	self._replicaRoot:SetAttribute("ChallengeDuration", report.ChallengeDuration)
	self._replicaRoot:SetAttribute("CoreHealthRemaining", report.CoreHealthRemaining)
	self._replicaRoot:SetAttribute("LeftLaneEnemyCount", report.LeftLaneEnemyCount)
	self._replicaRoot:SetAttribute("RightLaneEnemyCount", report.RightLaneEnemyCount)
	self._replicaRoot:SetAttribute("LeftLaneCoreHits", report.LeftLaneCoreHits)
	self._replicaRoot:SetAttribute("RightLaneCoreHits", report.RightLaneCoreHits)
	self._replicaRoot:SetAttribute("FirstBreachTime", report.FirstBreachTime)
	self._replicaRoot:SetAttribute("FirstBreachLane", report.FirstBreachLane)
	self._replicaRoot:SetAttribute("FirstBreachPadId", report.FirstBreachPadId)
	self._replicaRoot:SetAttribute("FirstBreachEnemyType", report.FirstBreachEnemyType)
	self._replicaRoot:SetAttribute("TotalWallDamageAbsorbed", report.TotalWallDamageAbsorbed)
	self._replicaRoot:SetAttribute("TotalTurretDamage", report.TotalTurretDamage)
	self._replicaRoot:SetAttribute("TotalEnemiesSlowed", report.TotalEnemiesSlowed)
	self._replicaRoot:SetAttribute("EnemiesReachedCore", report.EnemiesReachedCore)
	self._replicaRoot:SetAttribute("ReportReady", true)
	return report
end

return CombatStatsService
