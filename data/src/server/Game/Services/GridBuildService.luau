--!strict

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

type GameState = "PREPARATION" | "STARTING" | "DEFENDING" | "VICTORY" | "DEFEAT" | "REVIEW"
type PieceType = "Wall" | "SlowTrap" | "Turret"
type BuildPieceData = {
	id: string,
	pieceType: PieceType,
	cellX: number,
	cellZ: number,
	rotation: number,
}
type BuildPlan = { schemaVersion: number, revision: number, pieces: { [string]: BuildPieceData } }
type BuildOperation = "PLACE" | "MOVE" | "ROTATE" | "DELETE" | "UNDO" | "REDO" | "CLEAR_ALL"
type BuildRequest = {
	requestId: string,
	baseRevision: number,
	operation: BuildOperation,
	payload: { [string]: unknown },
}
type BuildResult = {
	requestId: string,
	success: boolean,
	reason: string?,
	revision: number,
	delta: unknown?,
	structureUsed: number,
	powerUsed: number,
}
type StateService = { getPhase: (self: StateService) -> GameState }
type Store = {
	GetPlan: (self: Store) -> BuildPlan,
	NewPieceId: (self: Store) -> string,
	CommitPieces: (self: Store, pieces: { [string]: BuildPieceData }) -> BuildPlan,
	Replace: (self: Store, plan: BuildPlan, preserveRevision: boolean) -> BuildPlan,
}
type History = {
	Record: (self: History, before: BuildPlan, after: BuildPlan) -> (),
	Undo: (self: History) -> BuildPlan?,
	Redo: (self: History) -> BuildPlan?,
	CanUndo: (self: History) -> boolean,
	CanRedo: (self: History) -> boolean,
}
type Renderer = { Render: (self: Renderer, BuildPlan) -> () }
type Validator = {
	Validate: (self: Validator, BuildPlan, BuildPieceData, string?) -> (boolean, string?),
}
type RulesModule = { CalculateBudgets: (BuildPlan) -> (number, number) }
type TypesModule = {
	isPieceType: (unknown) -> boolean,
	isRotation: (unknown) -> boolean,
}
type RequestPolicyModule = {
	Parse: (unknown) -> BuildRequest?,
	ReadRequestId: (unknown) -> string,
	ConsumeRateLimit: (RateWindow?, number, number) -> (RateWindow, boolean, boolean),
}
type GridConfig = {
	requestCacheLimit: number,
	requestRatePerSecond: number,
	structureLimit: number,
	powerLimit: number,
}
type PlanChangedCallback = (plan: BuildPlan) -> ()
type RateWindow = {
	startedAt: number,
	count: number,
	notificationSent: boolean,
}
type CachedResult = { result: BuildResult }

local sharedGame = ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Game")
local config = sharedGame:WaitForChild("Config")
local BuildGridConfig =
	require(config:WaitForChild("BuildGridConfig") :: ModuleScript) :: GridConfig
local BuildRules = require(sharedGame:WaitForChild("BuildRules") :: ModuleScript) :: RulesModule
local BuildTypes = require(sharedGame:WaitForChild("BuildTypes") :: ModuleScript) :: TypesModule
local servicesFolder = script.Parent
assert(
	servicesFolder and servicesFolder:IsA("Folder"),
	"GridBuildService must be under Game.Services"
)
local gameFolder = servicesFolder.Parent
assert(gameFolder and gameFolder:IsA("Folder"), "Game.Services must be under Game")
local buildFolder = gameFolder:WaitForChild("Build")
local BuildRequestPolicy =
	require(buildFolder:WaitForChild("BuildRequestPolicy") :: ModuleScript) :: RequestPolicyModule

local GridBuildService = {}
GridBuildService.__index = GridBuildService

export type Service = typeof(setmetatable(
	{} :: {
		_stateService: StateService,
		_replicaRoot: Folder,
		_buildResult: RemoteEvent,
		_store: Store,
		_history: History,
		_renderer: Renderer,
		_validator: Validator,
		_ownerUserId: number?,
		_buildEnabled: boolean,
		_processing: { [Player]: boolean },
		_rateWindows: { [Player]: RateWindow },
		_cache: { [Player]: { [string]: CachedResult } },
		_cacheOrder: { [Player]: { string } },
		_planChangedCallback: PlanChangedCallback?,
	},
	GridBuildService
))

local function clonePieces(pieces: { [string]: BuildPieceData }): { [string]: BuildPieceData }
	local result: { [string]: BuildPieceData } = {}
	for id, piece in pieces do
		result[id] = table.clone(piece)
	end
	return result
end

local function readInteger(value: unknown): number?
	return if typeof(value) == "number"
			and value > -math.huge
			and value < math.huge
			and value == math.floor(value)
		then value
		else nil
end

local function readShortString(value: unknown, limit: number): string?
	return if typeof(value) == "string" and #value > 0 and #value <= limit then value else nil
end

function GridBuildService.new(
	buildRequest: RemoteEvent,
	buildResult: RemoteEvent,
	stateService: StateService,
	replicaRoot: Folder,
	store: Store,
	history: History,
	renderer: Renderer,
	validator: Validator
): Service
	local self: Service = setmetatable({
		_stateService = stateService,
		_replicaRoot = replicaRoot,
		_buildResult = buildResult,
		_store = store,
		_history = history,
		_renderer = renderer,
		_validator = validator,
		_ownerUserId = nil,
		_buildEnabled = true,
		_processing = {},
		_rateWindows = {},
		_cache = {},
		_cacheOrder = {},
		_planChangedCallback = nil,
	}, GridBuildService)

	local function assignOwner(player: Player)
		if self._ownerUserId == nil then
			self._ownerUserId = player.UserId
			replicaRoot:SetAttribute("BuildOwnerUserId", player.UserId)
		end
		task.defer(function()
			if player.Parent == Players then
				self:_sendPlan(player, "SYNC", "INITIAL_SYNC")
			end
		end)
	end
	for _, player in Players:GetPlayers() do
		assignOwner(player)
	end
	Players.PlayerAdded:Connect(assignOwner)
	Players.PlayerRemoving:Connect(function(player: Player)
		self._processing[player] = nil
		self._rateWindows[player] = nil
		self._cache[player] = nil
		self._cacheOrder[player] = nil
		if self._ownerUserId == player.UserId then
			self._ownerUserId = nil
			for _, candidate in Players:GetPlayers() do
				if candidate ~= player then
					self._ownerUserId = candidate.UserId
					break
				end
			end
			replicaRoot:SetAttribute("BuildOwnerUserId", self._ownerUserId)
		end
	end)
	buildRequest.OnServerEvent:Connect(function(player: Player, requestValue: unknown)
		self:_handleRequest(player, requestValue)
	end)

	replicaRoot:SetAttribute("StructureUsed", 0)
	replicaRoot:SetAttribute("StructureMax", BuildGridConfig.structureLimit)
	replicaRoot:SetAttribute("PowerUsed", 0)
	replicaRoot:SetAttribute("PowerMax", BuildGridConfig.powerLimit)
	replicaRoot:SetAttribute("BuildRevision", 0)
	replicaRoot:SetAttribute("BuildEnabled", true)
	renderer:Render(store:GetPlan())
	return self
end

function GridBuildService.setPlanChangedCallback(self: Service, callback: PlanChangedCallback)
	self._planChangedCallback = callback
	callback(self._store:GetPlan())
end

function GridBuildService.getPlan(self: Service): BuildPlan
	return self._store:GetPlan()
end

function GridBuildService.isOwner(self: Service, player: Player): boolean
	return player.Parent == Players and self._ownerUserId == player.UserId
end

function GridBuildService.snapshot(self: Service): BuildPlan
	return self._store:GetPlan()
end

function GridBuildService.restore(self: Service, plan: BuildPlan)
	local restored = self._store:Replace(plan, true)
	self._renderer:Render(restored)
	if self._planChangedCallback then
		self._planChangedCallback(restored)
	end
	local structure, power = BuildRules.CalculateBudgets(restored)
	self._replicaRoot:SetAttribute("StructureUsed", structure)
	self._replicaRoot:SetAttribute("PowerUsed", power)
	self._replicaRoot:SetAttribute("BuildRevision", restored.revision)
	self._buildResult:FireAllClients(self:_makeResult("SYNC", true, "PLAN_RESTORED", restored))
end

function GridBuildService.setBuildEnabled(self: Service, enabled: boolean)
	self._buildEnabled = enabled
	self._replicaRoot:SetAttribute("BuildEnabled", enabled)
end

function GridBuildService._isRateLimited(self: Service, player: Player): (boolean, boolean)
	local window, limited, shouldNotify = BuildRequestPolicy.ConsumeRateLimit(
		self._rateWindows[player],
		os.clock(),
		BuildGridConfig.requestRatePerSecond
	)
	self._rateWindows[player] = window
	return limited, shouldNotify
end

function GridBuildService._parseRequest(_self: Service, requestValue: unknown): BuildRequest?
	return BuildRequestPolicy.Parse(requestValue)
end

function GridBuildService._makeResult(
	self: Service,
	requestId: string,
	success: boolean,
	reason: string?,
	plan: BuildPlan
): BuildResult
	local structure, power = BuildRules.CalculateBudgets(plan)
	return {
		requestId = requestId,
		success = success,
		reason = reason,
		revision = plan.revision,
		delta = {
			plan = plan,
			canUndo = self._history:CanUndo(),
			canRedo = self._history:CanRedo(),
		},
		structureUsed = structure,
		powerUsed = power,
	}
end

function GridBuildService._cacheResult(
	self: Service,
	player: Player,
	requestId: string,
	result: BuildResult
)
	local cache: { [string]: CachedResult } = self._cache[player] or {}
	local order: { string } = self._cacheOrder[player] or {}
	self._cache[player] = cache
	self._cacheOrder[player] = order
	if not cache[requestId] then
		table.insert(order, requestId)
	end
	cache[requestId] = { result = result }
	while #order > BuildGridConfig.requestCacheLimit do
		local evicted = table.remove(order, 1)
		if evicted then
			cache[evicted] = nil
		end
	end
end

function GridBuildService._sendPlan(
	self: Service,
	player: Player,
	requestId: string,
	reason: string?
)
	self._buildResult:FireClient(
		player,
		self:_makeResult(requestId, true, reason, self._store:GetPlan())
	)
end

function GridBuildService._reject(self: Service, player: Player, requestId: string, reason: string)
	local result = self:_makeResult(requestId, false, reason, self._store:GetPlan())
	self:_cacheResult(player, requestId, result)
	self._buildResult:FireClient(player, result)
end

function GridBuildService._rejectWithoutPlan(
	self: Service,
	player: Player,
	requestId: string,
	reason: string
)
	local plan = self._store:GetPlan()
	local structure, power = BuildRules.CalculateBudgets(plan)
	self._buildResult:FireClient(player, {
		requestId = requestId,
		success = false,
		reason = reason,
		revision = plan.revision,
		delta = nil,
		structureUsed = structure,
		powerUsed = power,
	})
end

function GridBuildService._commit(
	self: Service,
	player: Player,
	requestId: string,
	before: BuildPlan,
	pieces: { [string]: BuildPieceData },
	recordHistory: boolean
)
	local after = self._store:CommitPieces(pieces)
	if recordHistory then
		self._history:Record(before, after)
	end
	self._renderer:Render(after)
	if self._planChangedCallback then
		self._planChangedCallback(after)
	end
	local structure, power = BuildRules.CalculateBudgets(after)
	self._replicaRoot:SetAttribute("StructureUsed", structure)
	self._replicaRoot:SetAttribute("PowerUsed", power)
	self._replicaRoot:SetAttribute("BuildRevision", after.revision)
	local result = self:_makeResult(requestId, true, nil, after)
	self:_cacheResult(player, requestId, result)
	self._buildResult:FireAllClients(result)
end

function GridBuildService._mutate(
	self: Service,
	request: BuildRequest,
	plan: BuildPlan
): ({ [string]: BuildPieceData }?, string?)
	local pieces = clonePieces(plan.pieces)
	local payload = request.payload
	if request.operation == "CLEAR_ALL" then
		return {}, nil
	elseif request.operation == "DELETE" then
		local pieceId = readShortString(payload.pieceId, 32)
		if not pieceId or not pieces[pieceId] then
			return nil, "INVALID_PIECE"
		end
		pieces[pieceId] = nil
		return pieces, nil
	end

	local piece: BuildPieceData
	local ignorePieceId: string? = nil
	if request.operation == "PLACE" then
		local pieceType = payload.pieceType
		local cellX = readInteger(payload.cellX)
		local cellZ = readInteger(payload.cellZ)
		local rotation = readInteger(payload.rotation)
		if
			not BuildTypes.isPieceType(pieceType)
			or not cellX
			or not cellZ
			or not rotation
			or not BuildTypes.isRotation(rotation)
		then
			return nil, "INVALID_PIECE"
		end
		piece = {
			id = self._store:NewPieceId(),
			pieceType = pieceType :: PieceType,
			cellX = cellX,
			cellZ = cellZ,
			rotation = rotation,
		}
	else
		local pieceId = readShortString(payload.pieceId, 32)
		local existing = if pieceId then pieces[pieceId] else nil
		if not pieceId or not existing then
			return nil, "INVALID_PIECE"
		end
		ignorePieceId = pieceId
		piece = table.clone(existing)
		if request.operation == "MOVE" then
			local cellX = readInteger(payload.cellX)
			local cellZ = readInteger(payload.cellZ)
			if not cellX or not cellZ then
				return nil, "INVALID_PIECE"
			end
			piece.cellX = cellX
			piece.cellZ = cellZ
		elseif request.operation == "ROTATE" then
			local rotation = readInteger(payload.rotation)
			if not rotation or not BuildTypes.isRotation(rotation) then
				return nil, "INVALID_ROTATION"
			end
			piece.rotation = rotation
		else
			return nil, "REQUEST_CONFLICT"
		end
	end

	local valid, reason = self._validator:Validate(plan, piece, ignorePieceId)
	if not valid then
		return nil, reason or "REQUEST_CONFLICT"
	end
	pieces[piece.id] = piece
	return pieces, nil
end

function GridBuildService._handleRequest(self: Service, player: Player, requestValue: unknown)
	if player.Parent ~= Players then
		return
	end
	local limited, shouldNotify = self:_isRateLimited(player)
	if limited then
		if shouldNotify then
			self:_rejectWithoutPlan(
				player,
				BuildRequestPolicy.ReadRequestId(requestValue),
				"RATE_LIMITED"
			)
		end
		return
	end
	if self._processing[player] then
		return
	end
	local request = self:_parseRequest(requestValue)
	if not request then
		self:_rejectWithoutPlan(
			player,
			BuildRequestPolicy.ReadRequestId(requestValue),
			"REQUEST_CONFLICT"
		)
		return
	end
	local playerCache = self._cache[player]
	local cached = if playerCache then playerCache[request.requestId] else nil
	if cached then
		self._buildResult:FireClient(player, cached.result)
		return
	end
	if self._ownerUserId ~= player.UserId then
		self:_reject(player, request.requestId, "NOT_OWNER")
		return
	end
	if not self._buildEnabled or self._stateService:getPhase() ~= "PREPARATION" then
		self:_reject(player, request.requestId, "WRONG_STATE")
		return
	end

	self._processing[player] = true
	local plan = self._store:GetPlan()
	if request.baseRevision ~= plan.revision then
		self._processing[player] = nil
		self:_reject(player, request.requestId, "STALE_REVISION")
		return
	end
	if request.operation == "UNDO" or request.operation == "REDO" then
		local target = if request.operation == "UNDO"
			then self._history:Undo()
			else self._history:Redo()
		if not target then
			self._processing[player] = nil
			self:_reject(player, request.requestId, "REQUEST_CONFLICT")
			return
		end
		self:_commit(player, request.requestId, plan, target.pieces, false)
		self._processing[player] = nil
		return
	end

	local pieces, reason = self:_mutate(request, plan)
	if not pieces then
		self._processing[player] = nil
		self:_reject(player, request.requestId, reason or "REQUEST_CONFLICT")
		return
	end
	self:_commit(player, request.requestId, plan, pieces, true)
	self._processing[player] = nil
end

return GridBuildService
