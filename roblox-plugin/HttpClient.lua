--!strict
-- Sends snapshots only to the local RoGraph service.

local HttpService = game:GetService("HttpService")

local HttpClient = {}
local SNAPSHOT_URL = "http://127.0.0.1:8765/api/studio/snapshot"

function HttpClient.postSnapshot(snapshot): (boolean, string)
	local ok, response = pcall(function()
		return HttpService:RequestAsync({
			Url = SNAPSHOT_URL,
			Method = "POST",
			Headers = { ["Content-Type"] = "application/json" },
			Body = HttpService:JSONEncode(snapshot),
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

return HttpClient
