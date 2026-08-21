--!strict
-- Save this Script as a local Studio plugin with Scanner, Serializer, and HttpClient modules beneath it.

assert(plugin, "RoGraph must run as a Roblox Studio plugin")

local HttpClient = require(script.HttpClient)
local Scanner = require(script.Scanner)
local ChangeTracker = require(script.ChangeTracker)

local toolbar = plugin:CreateToolbar("RoGraph")
local indexButton = toolbar:CreateButton("IndexProject", "Index this place in local RoGraph", "")
indexButton.ClickableWhenViewportHidden = true

local indexing = false
indexButton.Click:Connect(function()
	if indexing then
		return
	end
	indexing = true
	indexButton.Enabled = false

	local snapshot = Scanner.snapshot()
	local ok, result = HttpClient.postSnapshot(snapshot)
	if ok then
		print("[RoGraph] Indexed project: " .. result)
		ChangeTracker.start()
	else
		warn("[RoGraph] Indexing failed: " .. result)
	end

	indexing = false
	indexButton.Enabled = true
end)
