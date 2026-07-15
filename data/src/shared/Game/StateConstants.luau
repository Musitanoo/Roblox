--!strict

local StateConstants = {
	PREPARATION = "PREPARATION",
	STARTING = "STARTING",
	DEFENDING = "DEFENDING",
	VICTORY = "VICTORY",
	DEFEAT = "DEFEAT",
	REVIEW = "REVIEW",
}

return table.freeze(StateConstants)
