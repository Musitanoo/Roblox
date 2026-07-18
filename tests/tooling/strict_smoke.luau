--!strict

local function identity<T>(value: T): T
	return value
end

assert(identity("toolchain") == "toolchain", "generic identity must preserve the value")

return true
