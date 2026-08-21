--!strict
-- Converts Studio values into JSON-safe data without mutating the DataModel.

local Serializer = {}

local function serializeValue(value: any): any
	local valueType = typeof(value)
	if valueType == "string" or valueType == "number" or valueType == "boolean" then
		return value
	end
	return tostring(value)
end

function Serializer.attributes(instance: Instance): {[string]: any}
	local output: {[string]: any} = {}
	for name, value in instance:GetAttributes() do
		output[name] = serializeValue(value)
	end
	return output
end

function Serializer.source(instance: Instance): string?
	if not instance:IsA("LuaSourceContainer") then
		return nil
	end
	local ok, source = pcall(function()
		return instance.Source
	end)
	return if ok then source else nil
end

function Serializer.debugId(instance: Instance): string?
	local ok, id = pcall(function()
		return instance:GetDebugId(0)
	end)
	return if ok then id else nil
end

return Serializer
