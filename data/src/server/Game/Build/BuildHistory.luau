--!strict

local ReplicatedStorage = game:GetService("ReplicatedStorage")

type PieceType = "Wall" | "SlowTrap" | "Turret"
type BuildPieceData = {
	id: string,
	pieceType: PieceType,
	cellX: number,
	cellZ: number,
	rotation: number,
}
type BuildPlan = { schemaVersion: number, revision: number, pieces: { [string]: BuildPieceData } }
type Entry = { before: BuildPlan, after: BuildPlan }
type GridConfig = { historyLimit: number }

local sharedGame = ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Game")
local config = sharedGame:WaitForChild("Config")
local BuildGridConfig =
	require(config:WaitForChild("BuildGridConfig") :: ModuleScript) :: GridConfig

local BuildHistory = {}
BuildHistory.__index = BuildHistory

export type History = typeof(setmetatable(
	{} :: { _undo: { Entry }, _redo: { Entry } },
	BuildHistory
))

function BuildHistory.new(): History
	return setmetatable({ _undo = {}, _redo = {} }, BuildHistory)
end

function BuildHistory.Record(self: History, before: BuildPlan, after: BuildPlan)
	table.insert(self._undo, { before = before, after = after })
	while #self._undo > BuildGridConfig.historyLimit do
		table.remove(self._undo, 1)
	end
	table.clear(self._redo)
end

function BuildHistory.Undo(self: History): BuildPlan?
	local entry = table.remove(self._undo)
	if not entry then
		return nil
	end
	table.insert(self._redo, entry)
	return entry.before
end

function BuildHistory.Redo(self: History): BuildPlan?
	local entry = table.remove(self._redo)
	if not entry then
		return nil
	end
	table.insert(self._undo, entry)
	return entry.after
end

function BuildHistory.Clear(self: History)
	table.clear(self._undo)
	table.clear(self._redo)
end
function BuildHistory.CanUndo(self: History): boolean
	return #self._undo > 0
end
function BuildHistory.CanRedo(self: History): boolean
	return #self._redo > 0
end

return BuildHistory
