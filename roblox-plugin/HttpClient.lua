--!strict
-- Sends snapshots only to the local RoGraph service.

local HttpService = game:GetService("HttpService")

local HttpClient = {}
local SNAPSHOT_URL = "http://127.0.0.1:8765/api/studio/snapshot"
local EVENTS_URL = "http://127.0.0.1:8765/api/studio/events"

local function post(url: string, body): (boolean, string)
	local ok, response = pcall(function()
		return HttpService:RequestAsync({
			Url = url,
			Method = "POST",
			Headers = { ["Content-Type"] = "application/json" },
			Body = HttpService:JSONEncode(body),
		})
	end)
	if not ok then
		return false, tostring(response)
	end
	if not response.Success then
		return false, string.format("HTTP %d: %s", response.StatusCode, response.StatusMessage)
	end
	return true, response.Body
end

function HttpClient.postSnapshot(snapshot): (boolean, string)
	return post(SNAPSHOT_URL, snapshot)
end

function HttpClient.postEvent(event): (boolean, string)
	return post(EVENTS_URL, event)
end

return HttpClient
