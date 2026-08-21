--!strict
-- Reads meaningful architectural instances from the open DataModel.

local CollectionService = game:GetService("CollectionService")

local Serializer = require(script.Parent.Serializer)

local Scanner = {}

local architecturalClasses = {
	Script = true,
	LocalScript = true,
	ModuleScript = true,
	RemoteEvent = true,
	RemoteFunction = true,
	BindableEvent = true,
	BindableFunction = true,
	Folder = true,
	Model = true,
}

local function isArchitectural(instance: Instance): boolean
	return instance.ClassName ~= ""
		and (instance.Parent == game or architecturalClasses[instance.ClassName] == true)
end

local function record(instance: Instance)
	local tags: {string} = {}
	local tagsOk, result = pcall(function()
		return CollectionService:GetTags(instance)
	end)
	if tagsOk then
		tags = result
	end

	return {
		id = Serializer.debugId(instance),
		name = instance.Name,
		className = instance.ClassName,
		path = instance:GetFullName(),
		parentPath = if instance.Parent == game then "game" else instance.Parent:GetFullName(),
		isService = instance.Parent == game,
		source = Serializer.source(instance),
		attributes = Serializer.attributes(instance),
		tags = tags,
	}
end

function Scanner.snapshot()
	local instances = {}
	for _, instance in game:GetDescendants() do
		if isArchitectural(instance) then
			table.insert(instances, record(instance))
		end
	end

	local placeId = game.PlaceId ~= 0 and tostring(game.PlaceId) or nil
	return {
		project = {
			id = placeId and "place:" .. placeId or "studio:" .. game.Name,
			name = game.Name,
			place_id = placeId,
		},
		instances = instances,
	}
end

return Scanner
