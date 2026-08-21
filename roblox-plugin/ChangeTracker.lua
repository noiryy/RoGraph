--!strict
-- Sends debounced, meaningful DataModel changes to the local RoGraph bridge.

local CollectionService = game:GetService("CollectionService")

local HttpClient = require(script.Parent.HttpClient)
local Scanner = require(script.Parent.Scanner)

local ChangeTracker = {}
local DEBOUNCE_SECONDS = 0.75
local started = false
local revisions: {[Instance]: number} = {}
local lastKnownPaths: {[Instance]: string} = {}

local function postEvent(event): boolean
	local ok, result = HttpClient.postEvent(event)
	if not ok then
		warn("[RoGraph] Change update failed: " .. result)
	end
	return ok
end

local function sendUpsert(instance: Instance)
	if instance.Parent == nil or not Scanner.isArchitectural(instance) then
		return
	end
	local record = Scanner.record(instance)
	lastKnownPaths[instance] = record.path
	postEvent({ project_id = Scanner.project().id, kind = "upsert", instance = record })
end

local function schedule(instance: Instance)
	if not Scanner.isArchitectural(instance) then
		return
	end
	lastKnownPaths[instance] = instance:GetFullName()
	local revision = (revisions[instance] or 0) + 1
	revisions[instance] = revision
	task.delay(DEBOUNCE_SECONDS, function()
		if revisions[instance] == revision then
			sendUpsert(instance)
		end
	end)
end

local function trackInstance(instance: Instance)
	if not Scanner.isArchitectural(instance) then
		return
	end
	instance:GetPropertyChangedSignal("Name"):Connect(function()
		schedule(instance)
	end)
	instance:GetPropertyChangedSignal("Parent"):Connect(function()
		schedule(instance)
	end)
	instance.AttributeChanged:Connect(function()
		schedule(instance)
	end)
	if instance:IsA("LuaSourceContainer") then
		instance:GetPropertyChangedSignal("Source"):Connect(function()
			schedule(instance)
		end)
	end
end

function ChangeTracker.start()
	if started then
		return
	end
	started = true
	for _, instance in game:GetDescendants() do
		trackInstance(instance)
	end
	game.DescendantAdded:Connect(function(instance)
		trackInstance(instance)
		schedule(instance)
	end)
	game.DescendantRemoving:Connect(function(instance)
		if Scanner.isArchitectural(instance) then
			local path = lastKnownPaths[instance]
			if path then
				postEvent({ project_id = Scanner.project().id, kind = "remove", path = path })
			end
			lastKnownPaths[instance] = nil
		end
	end)
	for _, tag in CollectionService:GetAllTags() do
		CollectionService:GetInstanceAddedSignal(tag):Connect(schedule)
		CollectionService:GetInstanceRemovedSignal(tag):Connect(schedule)
	end
end

return ChangeTracker
