--!strict

local forbidden = {
	["8:1"] = true,
	["9:1"] = true,
	["8:2"] = true,
	["9:2"] = true,
	["8:4"] = true,
	["9:4"] = true,
	["8:5"] = true,
	["9:5"] = true,
	["8:7"] = true,
	["9:7"] = true,
	["8:8"] = true,
	["9:8"] = true,
}

local BuildGridConfig = {
	schemaVersion = 1,
	width = 16,
	depth = 12,
	cellSize = 4,
	structureLimit = 24,
	powerLimit = 8,
	historyLimit = 20,
	requestCacheLimit = 64,
	requestRatePerSecond = 10,
	buildSurfaceName = "BuildSurface",
	forbiddenCells = table.freeze(forbidden),
	startCells = table.freeze({
		Left = table.freeze({ x = 2, z = 12 }),
		Right = table.freeze({ x = 15, z = 12 }),
	}),
	goalCells = table.freeze({
		Left = table.freeze({ x = 7, z = 1 }),
		Right = table.freeze({ x = 10, z = 1 }),
	}),
}

return table.freeze(BuildGridConfig)
