--!strict

local ServerScriptService = game:GetService("ServerScriptService")

type BuildOperation = "PLACE" | "MOVE" | "ROTATE" | "DELETE" | "UNDO" | "REDO" | "CLEAR_ALL"
type BuildRequest = {
	requestId: string,
	baseRevision: number,
	operation: BuildOperation,
	payload: { [string]: unknown },
}
type RateWindow = {
	startedAt: number,
	count: number,
	notificationSent: boolean,
}
type BuildRequestPolicyModule = {
	Parse: (unknown) -> BuildRequest?,
	ReadRequestId: (unknown) -> string,
	ConsumeRateLimit: (RateWindow?, number, number) -> (RateWindow, boolean, boolean),
}

local serverRoot = ServerScriptService:WaitForChild("Server")
local gameFolder = serverRoot:WaitForChild("Game")
local buildFolder = gameFolder:WaitForChild("Build")
local BuildRequestPolicy =
	require(buildFolder:WaitForChild("BuildRequestPolicy") :: ModuleScript) :: BuildRequestPolicyModule

local BuildRequestPolicySpec = {}

local function expect(condition: boolean, message: string)
	if not condition then
		error(message, 2)
	end
end

function BuildRequestPolicySpec.run()
	local valid = BuildRequestPolicy.Parse({
		requestId = "owner-1",
		baseRevision = 0,
		operation = "PLACE",
		payload = {
			pieceType = "Wall",
			cellX = 2,
			cellZ = 3,
			rotation = 0,
		},
	})
	expect(valid ~= nil and valid.operation == "PLACE", "valid PLACE must parse")

	expect(BuildRequestPolicy.Parse({
		requestId = "extra-top-level",
		baseRevision = 0,
		operation = "UNDO",
		payload = {},
		unexpected = true,
	}) == nil, "unknown top-level keys must be rejected")
	expect(BuildRequestPolicy.Parse({
		requestId = "extra-payload",
		baseRevision = 0,
		operation = "DELETE",
		payload = { pieceId = "piece-1", unexpected = true },
	}) == nil, "unknown payload keys must be rejected")
	expect(BuildRequestPolicy.Parse({
		requestId = "nested-payload",
		baseRevision = 0,
		operation = "DELETE",
		payload = { pieceId = { nested = { nested = true } } },
	}) == nil, "nested payload tables must be rejected")
	expect(BuildRequestPolicy.Parse({
		requestId = "numeric-key",
		baseRevision = 0,
		operation = "UNDO",
		payload = { [1] = true },
	}) == nil, "numeric payload keys must be rejected")
	expect(BuildRequestPolicy.Parse({
		requestId = "infinite-revision",
		baseRevision = math.huge,
		operation = "UNDO",
		payload = {},
	}) == nil, "infinite revisions must be rejected")
	expect(
		BuildRequestPolicy.ReadRequestId({ requestId = string.rep("x", 65) }) == "INVALID",
		"oversized request IDs must not be reflected"
	)
	expect(BuildRequestPolicy.Parse({
		requestId = "SYNC",
		baseRevision = 0,
		operation = "UNDO",
		payload = {},
	}) == nil, "server-reserved request IDs must be rejected")
	expect(
		BuildRequestPolicy.ReadRequestId({ requestId = "SYNC" }) == "INVALID",
		"reserved IDs must not be reflected in lightweight rejection results"
	)

	local window: RateWindow? = nil
	for index = 1, 10 do
		local limited: boolean
		local notify: boolean
		window, limited, notify = BuildRequestPolicy.ConsumeRateLimit(window, index * 0.01, 10)
		expect(not limited and not notify, "requests inside the quota must pass")
	end

	local limited: boolean
	local notify: boolean
	window, limited, notify = BuildRequestPolicy.ConsumeRateLimit(window, 0.2, 10)
	expect(limited and notify, "first request above quota must notify once")
	window, limited, notify = BuildRequestPolicy.ConsumeRateLimit(window, 0.3, 10)
	expect(limited and not notify, "later requests above quota must be silent")
	local saturatedWindow = window
	assert(saturatedWindow, "rate window must exist after quota consumption")
	expect(saturatedWindow.count == 11, "rate-window count must stay bounded")

	window, limited, notify = BuildRequestPolicy.ConsumeRateLimit(saturatedWindow, 1.2, 10)
	local resetWindow = window
	assert(resetWindow, "rate window must exist after reset")
	expect(
		not limited and not notify and resetWindow.count == 1,
		"new windows must reset the quota"
	)
end

return table.freeze(BuildRequestPolicySpec)
