--!strict
-- Reads meaningful architectural instances from the open DataModel.

local CollectionService = game:GetService("CollectionService")

local Serializer = require(script.Parent.Serializer)

local Scanner = {}

local StarterGui = game:GetService("StarterGui")

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

local function isUiComponent(instance: Instance): boolean
	return instance:IsDescendantOf(StarterGui)
		and (instance:IsA("GuiBase2d") or instance:IsA("UIBase"))
end

function Scanner.isArchitectural(instance: Instance): boolean
	return instance.Name ~= ""
		and instance.ClassName ~= ""
		and (
			instance.Parent == game
			or architecturalClasses[instance.ClassName] == true
			or isUiComponent(instance)
		)
end

function Scanner.record(instance: Instance)
	local tags: {string} = {}
	local tagsOk, result = pcall(function()
		return CollectionService:GetTags(instance)
	end)
	if tagsOk then
		tags = result
	end

	local uiComponent = isUiComponent(instance)

	return {
		id = Serializer.debugId(instance),
		name = instance.Name,
		className = if uiComponent then "UIComponent" else instance.ClassName,
		instanceClassName = instance.ClassName,
		path = instance:GetFullName(),
		parentPath = if instance.Parent == game then "game" else instance.Parent:GetFullName(),
		isService = instance.Parent == game,
		source = Serializer.source(instance),
		attributes = Serializer.attributes(instance),
		tags = tags,
	}
end

function Scanner.project()
	local placeId = game.PlaceId ~= 0 and tostring(game.PlaceId) or nil
	return {
		id = placeId and "place:" .. placeId or "studio:" .. game.Name,
		name = game.Name,
		place_id = placeId,
	}
end

function Scanner.snapshot()
	local instances = {}
	for _, instance in game:GetDescendants() do
		if Scanner.isArchitectural(instance) then
			table.insert(instances, Scanner.record(instance))
		end
	end

	return {
		project = Scanner.project(),
		instances = instances,
	}
end

return Scanner
