--!strict

-- Place this LocalScript in StarterPlayerScripts with the generated modules and
-- LightingProfileService available from ReplicatedStorage.ArtDirectionTools.

local CaptureService = game:GetService("CaptureService")
local HttpService = game:GetService("HttpService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Workspace = game:GetService("Workspace")

local tools = ReplicatedStorage:WaitForChild("ArtDirectionTools")
local Config = require(tools:WaitForChild("ArtDirectionConfig"))
local LightingProfileService = require(tools:WaitForChild("LightingProfileService"))
local LightingProfiles = require(tools:WaitForChild("LightingProfiles"))

local scene = Workspace:WaitForChild("ArtDirectionGoldenScene")
local cameraFolder = scene:WaitForChild("ValidationCameras")
local currentCamera = Workspace.CurrentCamera
assert(currentCamera, "Workspace.CurrentCamera is missing")

local requestedResolutionId = script:GetAttribute("ResolutionId") or "mobile_landscape_hard"
local requested = nil
for _, resolution in Config.cameraRig.resolutions do
	if resolution.id == requestedResolutionId then
		requested = resolution
		break
	end
end
assert(requested, `Unknown ResolutionId {requestedResolutionId}`)
local viewport = currentCamera.ViewportSize
if math.abs(viewport.X - requested.width) > 2 or math.abs(viewport.Y - requested.height) > 2 then
	error(
		`Viewport is {viewport.X}x{viewport.Y}; configure Device Emulator to {requested.width}x{requested.height} before capture.`
	)
end

local jobs = {}
for _, cameraId in { "near", "mid", "far", "three_quarter" } do
	for profileId, _ in LightingProfiles.profiles do
		table.insert(
			jobs,
			{ cameraId = cameraId, profileId = profileId, resolutionId = requestedResolutionId }
		)
	end
end

local captures = {}
local manifest = {}
for index, job in jobs do
	local marker = cameraFolder:FindFirstChild(job.cameraId)
	assert(marker and marker:IsA("Camera"), `Missing camera marker {job.cameraId}`)
	local lightingResult = LightingProfileService.apply(job.profileId, LightingProfiles)
	if not lightingResult.ok then
		error(
			`Lighting profile {job.profileId} failed: {table.concat(lightingResult.issues, "; ")}`
		)
	end
	currentCamera.CameraType = Enum.CameraType.Scriptable
	currentCamera.FieldOfViewMode = Enum.FieldOfViewMode.Vertical
	currentCamera.FieldOfView = Config.cameraRig.fieldOfView.degrees
	currentCamera.CFrame = marker.CFrame
	task.wait(0.2)
	local ready = Instance.new("BindableEvent")
	CaptureService:TakeScreenshotCaptureAsync(function(capture)
		table.insert(captures, capture)
		table.insert(manifest, {
			index = index,
			cameraId = job.cameraId,
			profileId = job.profileId,
			resolutionId = job.resolutionId,
			viewport = { currentCamera.ViewportSize.X, currentCamera.ViewportSize.Y },
		})
		ready:Fire()
	end, {})
	ready.Event:Wait()
	ready:Destroy()
end

local existingManifest = scene:FindFirstChild("CaptureManifest")
local manifestValue: StringValue
if existingManifest and existingManifest:IsA("StringValue") then
	manifestValue = existingManifest
else
	if existingManifest then
		existingManifest:Destroy()
	end
	manifestValue = Instance.new("StringValue")
end
manifestValue.Name = "CaptureManifest"
manifestValue.Value =
	HttpService:JSONEncode({ status = "CAPTURED_REQUIRES_USER_SAVE", jobs = manifest })
manifestValue.Parent = scene

CaptureService:PromptSaveCapturesToGallery(captures, function(result)
	print(`Art direction capture save result: {tostring(result)}`)
end)
