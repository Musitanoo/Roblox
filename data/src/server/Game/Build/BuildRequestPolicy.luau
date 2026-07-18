--!strict

type BuildOperation = "PLACE" | "MOVE" | "ROTATE" | "DELETE" | "UNDO" | "REDO" | "CLEAR_ALL"
export type BuildRequest = {
	requestId: string,
	baseRevision: number,
	operation: BuildOperation,
	payload: { [string]: unknown },
}
export type RateWindow = {
	startedAt: number,
	count: number,
	notificationSent: boolean,
}
local TOP_LEVEL_KEYS: { [string]: boolean } = table.freeze({
	requestId = true,
	baseRevision = true,
	operation = true,
	payload = true,
})
local PAYLOAD_KEYS: { [string]: { [string]: boolean } } = table.freeze({
	PLACE = table.freeze({
		pieceType = true,
		cellX = true,
		cellZ = true,
		rotation = true,
	}),
	MOVE = table.freeze({
		pieceId = true,
		cellX = true,
		cellZ = true,
	}),
	ROTATE = table.freeze({
		pieceId = true,
		rotation = true,
	}),
	DELETE = table.freeze({
		pieceId = true,
	}),
	UNDO = table.freeze({}),
	REDO = table.freeze({}),
	CLEAR_ALL = table.freeze({}),
})

local BuildRequestPolicy = {}

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

local function readOperation(value: unknown): BuildOperation?
	if value == "PLACE" then
		return "PLACE"
	elseif value == "MOVE" then
		return "MOVE"
	elseif value == "ROTATE" then
		return "ROTATE"
	elseif value == "DELETE" then
		return "DELETE"
	elseif value == "UNDO" then
		return "UNDO"
	elseif value == "REDO" then
		return "REDO"
	elseif value == "CLEAR_ALL" then
		return "CLEAR_ALL"
	end
	return nil
end

local function hasOnlyAllowedKeys(
	value: { [string]: unknown },
	allowedKeys: { [string]: boolean },
	limit: number
): boolean
	local count = 0
	for key in value do
		count += 1
		if count > limit or typeof(key) ~= "string" or allowedKeys[key] ~= true then
			return false
		end
	end
	return true
end

function BuildRequestPolicy.ReadRequestId(requestValue: unknown): string
	if typeof(requestValue) ~= "table" then
		return "INVALID"
	end
	local requestTable = requestValue :: { [string]: unknown }
	local requestId = readShortString(requestTable.requestId, 64)
	return if requestId
			and requestId ~= "SYNC"
			and requestId ~= "INVALID"
		then requestId
		else "INVALID"
end

function BuildRequestPolicy.Parse(requestValue: unknown): BuildRequest?
	if typeof(requestValue) ~= "table" then
		return nil
	end
	local requestTable = requestValue :: { [string]: unknown }
	if not hasOnlyAllowedKeys(requestTable, TOP_LEVEL_KEYS, 4) then
		return nil
	end

	local requestId = readShortString(requestTable.requestId, 64)
	local baseRevision = readInteger(requestTable.baseRevision)
	local operation: BuildOperation? = readOperation(requestTable.operation)
	if
		not requestId
		or requestId == "SYNC"
		or requestId == "INVALID"
		or not baseRevision
		or baseRevision < 0
	then
		return nil
	end
	if not operation or typeof(requestTable.payload) ~= "table" then
		return nil
	end

	local payload = requestTable.payload :: { [string]: unknown }
	local allowedPayloadKeys = PAYLOAD_KEYS[operation]
	if not allowedPayloadKeys or not hasOnlyAllowedKeys(payload, allowedPayloadKeys, 4) then
		return nil
	end
	for _, payloadValue in payload do
		if typeof(payloadValue) == "table" then
			return nil
		end
	end

	return {
		requestId = requestId,
		baseRevision = baseRevision,
		operation = operation,
		payload = payload,
	}
end

function BuildRequestPolicy.ConsumeRateLimit(
	window: RateWindow?,
	now: number,
	requestsPerSecond: number
): (RateWindow, boolean, boolean)
	local limit = math.max(1, math.floor(requestsPerSecond))
	if not window or now < window.startedAt or now - window.startedAt >= 1 then
		return {
			startedAt = now,
			count = 1,
			notificationSent = false,
		}, false, false
	end

	window.count = math.min(window.count + 1, limit + 1)
	if window.count <= limit then
		return window, false, false
	end

	local shouldNotify = not window.notificationSent
	window.notificationSent = true
	return window, true, shouldNotify
end

return table.freeze(BuildRequestPolicy)
