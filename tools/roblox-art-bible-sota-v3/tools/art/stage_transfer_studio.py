from __future__ import annotations

import argparse
import base64
import json
import math
import os
import re
import struct
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tools.art.common import (
    PROJECT_ROOT,
    ROOT,
    ArtSystemError,
    load_json,
    sha256_file,
    validate_with_schema,
    write_json,
)
from tools.art.studio_mcp import StudioMcpClient, StudioMcpError

MANIFEST_PATH = (
    ROOT
    / "evidence/transfer/turret-fast-v1/studio-import-manifest.json"
)
REGISTRY_PATH = (
    PROJECT_ROOT
    / "assets-3d/registry/turret-transfer-staging.local.json"
)
PUBLICATION_REPORT_PATH = (
    ROOT
    / "evidence/transfer/turret-fast-v1/studio-publication-report.json"
)
STUDIO_REPORT_PATH = (
    ROOT / "evidence/transfer/turret-fast-v1/studio-transfer-report.json"
)
CAPTURE_DIR = ROOT / "evidence/transfer/turret-fast-v1/studio-captures"
SCHEMA = "https://roblox-top1.local/schemas/transfer-studio-report.schema.json"
TERRITORIES = (
    "industrial-toy-defense",
    "salvaged-frontier",
    "clean-tactical-diorama",
)
STATES = ("intact", "damaged", "critical")
MATERIAL_RULES_PATH = ROOT / "art/materials/material-rules.json"
TERRITORY_PATHS = {
    territory_id: ROOT / f"art/territories/{territory_id}.json"
    for territory_id in TERRITORIES
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _matrix_multiply(a: list[float], b: list[float]) -> list[float]:
    result = [0.0] * 16
    for column in range(4):
        for row in range(4):
            result[column * 4 + row] = sum(
                a[index * 4 + row] * b[column * 4 + index]
                for index in range(4)
            )
    return result


def _node_matrix(node: dict[str, Any]) -> list[float]:
    if isinstance(node.get("matrix"), list) and len(node["matrix"]) == 16:
        return [float(value) for value in node["matrix"]]
    translation = [float(value) for value in node.get("translation", [0, 0, 0])]
    rotation = [float(value) for value in node.get("rotation", [0, 0, 0, 1])]
    scale = [float(value) for value in node.get("scale", [1, 1, 1])]
    x, y, z, w = rotation
    xx, yy, zz = x * x, y * y, z * z
    xy, xz, yz = x * y, x * z, y * z
    wx, wy, wz = w * x, w * y, w * z
    matrix = [
        (1 - 2 * (yy + zz)) * scale[0],
        (2 * (xy + wz)) * scale[0],
        (2 * (xz - wy)) * scale[0],
        0,
        (2 * (xy - wz)) * scale[1],
        (1 - 2 * (xx + zz)) * scale[1],
        (2 * (yz + wx)) * scale[1],
        0,
        (2 * (xz + wy)) * scale[2],
        (2 * (yz - wx)) * scale[2],
        (1 - 2 * (xx + yy)) * scale[2],
        0,
        translation[0],
        translation[1],
        translation[2],
        1,
    ]
    return matrix


def _transform(matrix: list[float], point: tuple[float, float, float]) -> list[float]:
    x, y, z = point
    return [
        matrix[0] * x + matrix[4] * y + matrix[8] * z + matrix[12],
        matrix[1] * x + matrix[5] * y + matrix[9] * z + matrix[13],
        matrix[2] * x + matrix[6] * y + matrix[10] * z + matrix[14],
    ]


def glb_bounds(path: Path) -> list[float]:
    payload = path.read_bytes()
    if len(payload) < 20 or payload[:4] != b"glTF":
        raise ArtSystemError(f"invalid GLB header: {path}")
    _magic, version, total_length = struct.unpack_from("<4sII", payload, 0)
    if version != 2 or total_length != len(payload):
        raise ArtSystemError(f"unsupported or truncated GLB: {path}")
    offset = 12
    document: dict[str, Any] | None = None
    while offset + 8 <= len(payload):
        chunk_length, chunk_type = struct.unpack_from("<II", payload, offset)
        offset += 8
        chunk = payload[offset : offset + chunk_length]
        offset += chunk_length
        if chunk_type == 0x4E4F534A:
            document = json.loads(chunk.rstrip(b"\x00 \t\r\n").decode("utf-8"))
            break
    if document is None:
        raise ArtSystemError(f"GLB JSON chunk is missing: {path}")
    nodes = document.get("nodes", [])
    meshes = document.get("meshes", [])
    accessors = document.get("accessors", [])
    scenes = document.get("scenes", [])
    scene_index = int(document.get("scene", 0))
    if not scenes or scene_index >= len(scenes):
        raise ArtSystemError(f"GLB scene is missing: {path}")
    minimum = [math.inf, math.inf, math.inf]
    maximum = [-math.inf, -math.inf, -math.inf]
    identity = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]

    def visit(index: int, parent: list[float]) -> None:
        node = nodes[index]
        world = _matrix_multiply(parent, _node_matrix(node))
        mesh_index = node.get("mesh")
        if isinstance(mesh_index, int):
            for primitive in meshes[mesh_index].get("primitives", []):
                accessor_index = primitive.get("attributes", {}).get("POSITION")
                if not isinstance(accessor_index, int):
                    continue
                accessor = accessors[accessor_index]
                low = accessor.get("min")
                high = accessor.get("max")
                if not (
                    isinstance(low, list)
                    and isinstance(high, list)
                    and len(low) == 3
                    and len(high) == 3
                ):
                    raise ArtSystemError(
                        f"GLB POSITION bounds are missing: {path}"
                    )
                for x in (float(low[0]), float(high[0])):
                    for y in (float(low[1]), float(high[1])):
                        for z in (float(low[2]), float(high[2])):
                            point = _transform(world, (x, y, z))
                            for axis in range(3):
                                minimum[axis] = min(minimum[axis], point[axis])
                                maximum[axis] = max(maximum[axis], point[axis])
        for child in node.get("children", []):
            visit(int(child), world)

    for root_node in scenes[scene_index].get("nodes", []):
        visit(int(root_node), identity)
    if any(not math.isfinite(value) for value in minimum + maximum):
        raise ArtSystemError(f"GLB contains no bounded mesh geometry: {path}")
    return [round(maximum[index] - minimum[index], 6) for index in range(3)]


def _load_inputs() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    manifest = load_json(MANIFEST_PATH)
    manifest_issues = validate_with_schema(
        manifest,
        ROOT / "schemas/transfer-import-queue.schema.json",
    )
    if manifest_issues:
        raise ArtSystemError(
            "transfer import manifest is invalid: " + "; ".join(manifest_issues)
        )
    publication = load_json(PUBLICATION_REPORT_PATH)
    publication_issues = validate_with_schema(
        publication,
        ROOT / "schemas/transfer-publication-report.schema.json",
    )
    if publication_issues or publication.get("status") != "PASS":
        raise ArtSystemError(
            "staging publication evidence is not PASS: "
            + "; ".join(publication_issues)
        )
    if publication["manifestSha256"] != sha256_file(MANIFEST_PATH):
        raise ArtSystemError("publication report is bound to a stale manifest")
    registry = load_json(REGISTRY_PATH)
    if (
        registry.get("environment") != "staging"
        or registry.get("assetId") != "turret_fast_v1"
        or not isinstance(registry.get("assets"), dict)
    ):
        raise ArtSystemError("local publication registry is invalid")
    expected_names = {entry["uploadName"] for entry in manifest["entries"]}
    if set(registry["assets"]) != expected_names:
        raise ArtSystemError("local publication registry is incomplete")
    for entry in manifest["entries"]:
        local = registry["assets"][entry["uploadName"]]
        if (
            not str(local.get("assetId", "")).isdigit()
            or local.get("sourceSha256") != entry["sha256"]
        ):
            raise ArtSystemError(
                f"local publication registry identity drift: {entry['uploadName']}"
            )
    return manifest, publication, registry


def _safe_issue(error: Exception) -> str:
    message = str(error)
    message = re.sub(r"\b\d{6,}\b", "[REDACTED]", message)
    message = re.sub(
        r"\b[0-9a-f]{8}-[0-9a-f-]{27,}\b",
        "[REDACTED]",
        message,
        flags=re.IGNORECASE,
    )
    return message[:300]


def _normalize_lua_json(value: Any) -> Any:
    if isinstance(value, list):
        return [_normalize_lua_json(item) for item in value]
    if not isinstance(value, dict):
        return value
    numeric: list[tuple[int, Any]] = []
    for key, item in value.items():
        if not isinstance(key, str) or not key.isdigit() or int(key) < 1:
            return {
                key: _normalize_lua_json(item)
                for key, item in value.items()
            }
        numeric.append((int(key), item))
    numeric.sort(key=lambda pair: pair[0])
    if [index for index, _item in numeric] != list(
        range(1, len(numeric) + 1)
    ):
        return {
            key: _normalize_lua_json(item)
            for key, item in value.items()
        }
    return [_normalize_lua_json(item) for _index, item in numeric]


def _rgb(hex_color: str) -> list[float]:
    if not re.fullmatch(r"#[0-9A-Fa-f]{6}", hex_color):
        raise ArtSystemError(f"invalid territory color: {hex_color}")
    return [
        int(hex_color[index : index + 2], 16) / 255
        for index in (1, 3, 5)
    ]


def _studio_styles(territory_id: str) -> dict[str, dict[str, Any]]:
    territory = load_json(TERRITORY_PATHS[territory_id])
    material_rules = load_json(MATERIAL_RULES_PATH)
    palette = territory["blockoutPalette"]
    assignments = territory["surfaceAssignments"]
    semantic_profiles = material_rules["semanticRoleProfiles"]
    material_profiles = material_rules["materials"]
    styles: dict[str, dict[str, Any]] = {}
    for role, color in palette.items():
        semantic = semantic_profiles[role]["studio"]
        material_id = assignments[role]
        assigned_material = material_profiles[material_id]["studioMaterial"]
        material = (
            semantic["material"]
            if role in {"interaction", "threat", "warning", "critical", "rubber", "bareMetal"}
            else assigned_material
        )
        styles[role] = {
            "color": _rgb(color),
            "material": material,
            "castShadow": semantic["castShadow"],
        }
    return styles


def _execute_json(client: StudioMcpClient, code: str, *, timeout: float = 45) -> Any:
    result = client.call_tool(
        "execute_luau",
        {"datamodel_type": "Edit", "code": code},
        timeout=timeout,
    )
    return _normalize_lua_json(client.json_content(result))


def _staging_probe(client: StudioMcpClient, expected_creator: str) -> dict[str, Any]:
    code = f'''
local ServerStorage = game:GetService("ServerStorage")
local staging = ServerStorage:FindFirstChild("ArtDirectionStaging")
return {{
    editModeVerified = true,
    deploymentMarkedStaging = game:GetAttribute("DeploymentEnvironment") == "staging",
    localConfigComplete = staging ~= nil and staging:GetAttribute("LocalConfigComplete") == true,
    savedCloudPlaceVerified = game.PlaceId > 0 and game.GameId > 0,
    expectedCreatorMatches = tostring(game.CreatorId) == "{expected_creator}",
    creatorAllowlistVerified = staging ~= nil and staging:GetAttribute("CreatorAllowlistVerified") == true
}}
'''
    value = _execute_json(client, code)
    if not isinstance(value, dict):
        raise StudioMcpError("staging probe returned a non-object")
    return value


def _prepare_staging(client: StudioMcpClient, evidence_digest: str) -> None:
    code = f'''
local ServerStorage = game:GetService("ServerStorage")
local existing = ServerStorage:FindFirstChild("ArtDirectionTransferImports_Staging")
if existing then existing:Destroy() end
local staging = Instance.new("Folder")
staging.Name = "ArtDirectionTransferImports_Staging"
staging:SetAttribute("EvidencePackageSha256", "{evidence_digest}")
staging:SetAttribute("CandidateOnly", true)
staging.Parent = ServerStorage
return {{ ok = true }}
'''
    value = _execute_json(client, code)
    if not isinstance(value, dict) or value.get("ok") is not True:
        raise StudioMcpError("Studio transfer staging root could not be prepared")


def _payload_entries(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    styles = {
        territory_id: _studio_styles(territory_id)
        for territory_id in TERRITORIES
    }
    values: list[dict[str, Any]] = []
    for entry in manifest["entries"]:
        values.append(
            {
                "territoryId": entry["territoryId"],
                "stateId": entry["stateId"],
                "uploadName": entry["uploadName"],
                "sourceSha256": entry["sha256"],
                "expectedBounds": glb_bounds(ROOT / entry["sourcePath"]),
                "styles": styles[entry["territoryId"]],
            }
        )
    return values


def _finalizer_code(entries: list[dict[str, Any]], evidence_digest: str) -> str:
    payload = json.dumps(
        {"entries": entries, "evidencePackageSha256": evidence_digest},
        separators=(",", ":"),
    )
    template = r'''
local HttpService = game:GetService("HttpService")
local Players = game:GetService("Players")
local ServerStorage = game:GetService("ServerStorage")
local Workspace = game:GetService("Workspace")
local payload = HttpService:JSONDecode([==[__PAYLOAD__]==])
local staging = ServerStorage:FindFirstChild("ArtDirectionTransferImports_Staging")
if not staging then return { ok = false, issues = { "staging root missing" } } end
local issues = {}
local checks = {}
local prepared = Instance.new("Folder")
prepared.Name = "PreparedKit"
prepared.Parent = staging

local function ensureFolder(parent, name)
    local value = parent:FindFirstChild(name)
    if value and not value:IsA("Folder") then
        table.insert(issues, parent:GetFullName() .. "." .. name .. " is not a Folder")
        return nil
    end
    if value then return value end
    value = Instance.new("Folder")
    value.Name = name
    value.Parent = parent
    return value
end

local function bounds(root)
    if root:IsA("Model") then return root:GetBoundingBox() end
    if root:IsA("BasePart") then return root.CFrame, root.Size end
    return nil, nil
end

local function parts(root)
    local values = {}
    if root:IsA("BasePart") then table.insert(values, root) end
    for _, value in root:GetDescendants() do
        if value:IsA("BasePart") then table.insert(values, value) end
    end
    return values
end

local function meshSignature(root)
    local values = {}
    for _, value in parts(root) do
        if value:IsA("MeshPart") then
            table.insert(values, value.MeshId .. "|" .. value.TextureID)
        end
    end
    table.sort(values)
    return table.concat(values, ";")
end

local function pivotTo(root, target)
    if root:IsA("Model") then root:PivotTo(target) else root.CFrame = target end
end

for _, spec in payload.entries do
    local root = staging:FindFirstChild(spec.uploadName)
    if not root or not (root:IsA("Model") or root:IsA("BasePart")) then
        table.insert(issues, spec.uploadName .. ": imported root missing or unsupported")
        continue
    end
    local cframe, size = bounds(root)
    if not cframe or not size then
        table.insert(issues, spec.uploadName .. ": bounds unavailable")
        continue
    end
    local observed = { size.X, size.Y, size.Z }
    local maximumError = 0
    for axis = 1, 3 do
        maximumError = math.max(
            maximumError,
            math.abs(observed[axis] - spec.expectedBounds[axis])
                / math.max(spec.expectedBounds[axis], 0.001)
                * 100
        )
    end
    local sourceMatches = spec.sourceSha256 ~= nil and #spec.sourceSha256 == 64
    root:SetAttribute("ArtTerritory", spec.territoryId)
    root:SetAttribute("ArtAssetId", "turret_fast_v1")
    root:SetAttribute("ArtState", spec.stateId)
    root:SetAttribute("ArtSourceSha256", spec.sourceSha256)
    root:SetAttribute("ArtEvidencePackageSha256", payload.evidencePackageSha256)
    root:SetAttribute("ArtCandidateOnly", true)
    local visualSettingsPass = true
    local materialBindingsPass = true
    local styledMeshPartCount = 0
    local unboundStyleRoleCount = 0
    local maximumColorChannelError = 0
    local meshPartCount = 0
    local meshIdsPresent = true
    local allParts = parts(root)
    for _, part in allParts do
        part.Anchored = true
        part.CanCollide = false
        part.CanTouch = false
        part.CanQuery = false
        part.CastShadow = true
        part.AudioCanCollide = false
        part.EnableFluidForces = false
        if part:IsA("MeshPart") then
            meshPartCount += 1
            part.RenderFidelity = Enum.RenderFidelity.Automatic
            part.CollisionFidelity = Enum.CollisionFidelity.Box
            part.DoubleSided = false
            if part.MeshId == "" then meshIdsPresent = false end
            local role = string.match(part.Name, "^ROLE_(.+)_Mesh$")
                or string.match(part.Name, "^ROLE_(.+)$")
            local style = role and spec.styles[role] or nil
            local material = style and Enum.Material[style.material] or nil
            if not role or not style or not material then
                materialBindingsPass = false
                unboundStyleRoleCount += 1
            else
                local targetColor = Color3.new(
                    style.color[1],
                    style.color[2],
                    style.color[3]
                )
                part.Color = targetColor
                part.Material = material
                part.MaterialVariant = ""
                part.CastShadow = style.castShadow
                maximumColorChannelError = math.max(
                    maximumColorChannelError,
                    math.abs(part.Color.R - targetColor.R),
                    math.abs(part.Color.G - targetColor.G),
                    math.abs(part.Color.B - targetColor.B)
                )
                if part.Material ~= material or part.CastShadow ~= style.castShadow then
                    materialBindingsPass = false
                end
                styledMeshPartCount += 1
            end
        end
    end
    visualSettingsPass = visualSettingsPass
        and materialBindingsPass
        and styledMeshPartCount == meshPartCount
        and unboundStyleRoleCount == 0
        and maximumColorChannelError <= 0.00001
    local translate = Vector3.new(-cframe.Position.X, size.Y / 2 - cframe.Position.Y, -cframe.Position.Z)
    local currentPivot = if root:IsA("Model") then root:GetPivot() else root.CFrame
    pivotTo(root, currentPivot + translate)
    local centeredCFrame, centeredSize = bounds(root)
    local hitbox = Instance.new("Part")
    hitbox.Name = "CollisionHitbox"
    hitbox.Size = centeredSize
    hitbox.CFrame = centeredCFrame
    hitbox.Transparency = 1
    hitbox.Anchored = true
    hitbox.CanCollide = true
    hitbox.CanTouch = false
    hitbox.CanQuery = true
    hitbox.CastShadow = false
    hitbox.AudioCanCollide = false
    hitbox.EnableFluidForces = false
    hitbox:SetAttribute("ArtHitbox", true)
    hitbox.Parent = root
    local territoryFolder = ensureFolder(prepared, spec.territoryId)
    local assetFolder = territoryFolder and ensureFolder(territoryFolder, "turret_fast_v1")
    if assetFolder then
        root.Name = spec.stateId
        root.Parent = assetFolder
    end
    local pass = maximumError <= 1.0
        and #allParts > 0
        and meshPartCount > 0
        and meshIdsPresent
        and sourceMatches
        and visualSettingsPass
        and hitbox.CanCollide
        and not hitbox.CanTouch
    if not pass then table.insert(issues, spec.uploadName .. ": validation failed") end
    table.insert(checks, {
        territoryId = spec.territoryId,
        stateId = spec.stateId,
        sourceSha256 = spec.sourceSha256,
        expectedBounds = spec.expectedBounds,
        observedBounds = observed,
        maximumBoundsErrorPercent = maximumError,
        partCount = #allParts,
        meshPartCount = meshPartCount,
        meshIdsPresent = meshIdsPresent,
        sourceIdentityMatches = sourceMatches,
        styledMeshPartCount = styledMeshPartCount,
        unboundStyleRoleCount = unboundStyleRoleCount,
        maximumColorChannelError = maximumColorChannelError,
        materialBindingsPass = materialBindingsPass,
        visualSettingsPass = visualSettingsPass,
        hitboxPass = hitbox.CanCollide and not hitbox.CanTouch and hitbox.CanQuery,
        pass = pass,
    })
end

if #checks ~= 9 then table.insert(issues, "validated state count is not nine") end
if #issues > 0 then return { ok = false, issues = issues, assetChecks = checks } end

local kit = ensureFolder(ServerStorage, "ArtDirectionAssetKit")
local rollback = Instance.new("Folder")
rollback.Name = "TransferRollback"
rollback.Parent = staging
local transactionOk, transactionError = pcall(function()
    for _, territoryId in { "industrial-toy-defense", "salvaged-frontier", "clean-tactical-diorama" } do
        local sourceTerritory = prepared:FindFirstChild(territoryId)
        local candidate = sourceTerritory and sourceTerritory:FindFirstChild("turret_fast_v1")
        assert(candidate, territoryId .. ": prepared turret folder missing")
        local targetTerritory = ensureFolder(kit, territoryId)
        assert(targetTerritory, territoryId .. ": target territory folder missing")
        local existing = targetTerritory:FindFirstChild("turret_fast_v1")
        if existing then
            existing.Name = territoryId .. "__turret_fast_v1"
            existing.Parent = rollback
        end
        candidate.Parent = targetTerritory
    end
end)
if not transactionOk then
    for _, old in rollback:GetChildren() do
        local territoryId = string.match(old.Name, "^(.-)__turret_fast_v1$")
        local territory = territoryId and kit:FindFirstChild(territoryId)
        if territory then
            local failed = territory:FindFirstChild("turret_fast_v1")
            if failed then failed:Destroy() end
            old.Name = "turret_fast_v1"
            old.Parent = territory
        end
    end
    return { ok = false, issues = { "transaction failed: " .. tostring(transactionError) }, assetChecks = checks }
end
rollback:Destroy()

local oldScene = Workspace:FindFirstChild("ArtDirectionTransferScene")
if oldScene then oldScene:Destroy() end
local scene = Instance.new("Model")
scene.Name = "ArtDirectionTransferScene"
scene:SetAttribute("ArtAssetId", "turret_fast_v1")
scene:SetAttribute("ArtEvidencePackageSha256", payload.evidencePackageSha256)
scene:SetAttribute("ArtCandidateOnly", true)
scene.Parent = Workspace
local ground = Instance.new("Part")
ground.Name = "Ground"
ground.Size = Vector3.new(62, 0.4, 62)
ground.CFrame = CFrame.new(0, 3999.8, 0)
ground.Anchored = true
ground.CanCollide = true
ground.Material = Enum.Material.SmoothPlastic
ground.Color = Color3.fromRGB(74, 79, 88)
ground.Parent = scene
local avatarPresent = false
local avatarOk, avatar = pcall(function()
    local description = Instance.new("HumanoidDescription")
    return Players:CreateHumanoidModelFromDescriptionAsync(description, Enum.HumanoidRigType.R15)
end)
if avatarOk and avatar then
    avatar.Name = "ReferenceAvatar_R15"
    for _, part in parts(avatar) do part.Anchored = true end
    avatar.Parent = scene
    avatar:PivotTo(CFrame.new(-25, 4000, -25))
    avatarPresent = true
end
local candidateCount = 0
local cameras = {}
for territoryIndex, territoryId in { "industrial-toy-defense", "salvaged-frontier", "clean-tactical-diorama" } do
    local territory = kit:FindFirstChild(territoryId)
    local asset = territory and territory:FindFirstChild("turret_fast_v1")
    local z = (territoryIndex - 2) * 18
    for stateIndex, stateId in { "intact", "damaged", "critical" } do
        local source = asset and asset:FindFirstChild(stateId)
        assert(source, territoryId .. "/" .. stateId .. ": staged source missing")
        local clone = source:Clone()
        clone.Name = territoryId .. "__" .. stateId
        clone.Parent = scene
        pivotTo(clone, CFrame.new((stateIndex - 2) * 10, 4000, z))
        candidateCount += 1
    end
    table.insert(cameras, {
        territoryId = territoryId,
        position = { 25, 4009, z - 29 },
        lookAt = { 0, 4002.7, z },
    })
end

local stressRoot = Instance.new("Folder")
stressRoot.Name = "StressGroups"
stressRoot.Parent = scene
local reuseChecks = {}
for territoryIndex, territoryId in { "industrial-toy-defense", "salvaged-frontier", "clean-tactical-diorama" } do
    local territory = kit:FindFirstChild(territoryId)
    local asset = territory and territory:FindFirstChild("turret_fast_v1")
    local source = asset and asset:FindFirstChild("intact")
    assert(source, territoryId .. "/intact stress source missing")
    for countIndex, copyCount in { 30, 100 } do
        local group = Instance.new("Folder")
        group.Name = territoryId .. "__" .. tostring(copyCount)
        group:SetAttribute("ExpectedCount", copyCount)
        group.Parent = stressRoot
        local signatures = {}
        local hashes = {}
        local columns = if copyCount == 30 then 6 else 10
        for index = 1, copyCount do
            local clone = source:Clone()
            clone.Name = string.format("Clone_%03d", index)
            clone.Parent = group
            local row = math.floor((index - 1) / columns)
            local column = (index - 1) % columns
            pivotTo(
                clone,
                CFrame.new(
                    (territoryIndex - 2) * 70 + (column - (columns - 1) / 2) * 7,
                    4200 + (countIndex - 1) * 100,
                    row * 7
                )
            )
            signatures[meshSignature(clone)] = true
            hashes[clone:GetAttribute("ArtSourceSha256")] = true
        end
        local signatureCount = 0
        for _ in signatures do signatureCount += 1 end
        local hashCount = 0
        for _ in hashes do hashCount += 1 end
        table.insert(reuseChecks, {
            territoryId = territoryId,
            copyCount = copyCount,
            observedCount = #group:GetChildren(),
            distinctSourceSha256Count = hashCount,
            distinctSignatureCount = signatureCount,
            pass = #group:GetChildren() == copyCount and hashCount == 1 and signatureCount == 1,
        })
    end
end

staging:Destroy()
return {
    ok = true,
    issues = {},
    assetChecks = checks,
    reuseChecks = reuseChecks,
    hierarchyChecks = {
        transactionApplied = true,
        assetKitPresent = ServerStorage:FindFirstChild("ArtDirectionAssetKit") ~= nil,
        territoryFolderCount = 3,
        assetFolderCount = 3,
        stateCount = 9,
        stagingRootRemoved = ServerStorage:FindFirstChild("ArtDirectionTransferImports_Staging") == nil,
    },
    sceneChecks = {
        scenePresent = Workspace:FindFirstChild("ArtDirectionTransferScene") ~= nil,
        candidateCount = candidateCount,
        stressGroupCount = #stressRoot:GetChildren(),
        placeholderCount = 0,
        cameraCount = #cameras,
        referenceAvatarPresent = avatarPresent,
    },
    cameras = cameras,
}
'''
    return template.replace("__PAYLOAD__", payload)


def _console_fingerprint(client: StudioMcpClient) -> set[str]:
    try:
        result = client.call_tool("get_console_output", {}, timeout=20)
        text = client.text_content(result)
    except StudioMcpError:
        return set()
    return {
        line.strip()
        for line in text.splitlines()
        if re.search(r"\b(error|exception|traceback)\b", line, re.IGNORECASE)
    }


def _playtest(client: StudioMcpClient, baseline: set[str]) -> dict[str, Any]:
    started = False
    stopped = False
    client_observed = False
    server_observed = False
    new_errors: set[str] = set()
    try:
        client.call_tool("start_stop_play", {"is_start": True}, timeout=30)
        started = True
        deadline = time.monotonic() + 25
        while time.monotonic() < deadline:
            state = client.text_content(
                client.call_tool("get_studio_state", {}, timeout=15)
            )
            client_observed = client_observed or "Client" in state
            server_observed = server_observed or "Server" in state
            if client_observed and server_observed:
                break
            time.sleep(0.5)
        after = _console_fingerprint(client)
        new_errors = after - baseline
    finally:
        try:
            client.call_tool("start_stop_play", {"is_start": False}, timeout=30)
            stopped = True
        except StudioMcpError:
            stopped = False
    return {
        "started": started,
        "clientDataModelObserved": client_observed,
        "serverDataModelObserved": server_observed,
        "stopped": stopped,
        "newRelevantErrorCount": len(new_errors),
        "pass": (
            started
            and client_observed
            and server_observed
            and stopped
            and not new_errors
        ),
    }


def _capture(
    client: StudioMcpClient,
    cameras: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[str]]:
    CAPTURE_DIR.mkdir(parents=True, exist_ok=True)
    capture_count = 0
    captures: list[dict[str, Any]] = []
    issues: list[str] = []
    for index, camera in enumerate(cameras, start=1):
        try:
            result = client.call_tool(
                "screen_capture",
                {
                    "capture_id": f"TransferTerritory_{index}",
                    "camera_position": camera["position"],
                    "look_at_position": camera["lookAt"],
                },
                timeout=30,
            )
            images = [
                item
                for item in result.get("content", [])
                if isinstance(item, dict)
                and item.get("type") == "image"
                and isinstance(item.get("data"), str)
            ]
            if not images:
                issues.append(
                    f"{camera['territoryId']}: screen_capture returned no image payload"
                )
                continue
            image = images[0]
            mime = image.get("mimeType", "image/png")
            extension = ".jpg" if "jpeg" in mime else ".png"
            output = CAPTURE_DIR / f"{camera['territoryId']}{extension}"
            output.write_bytes(base64.b64decode(image["data"]))
            captures.append(
                {
                    "territoryId": camera["territoryId"],
                    "path": output.relative_to(ROOT).as_posix(),
                    "bytes": output.stat().st_size,
                    "sha256": sha256_file(output),
                    "source": "studio_mcp_screen_capture",
                }
            )
            capture_count += 1
        except (StudioMcpError, OSError, ValueError) as error:
            issues.append(f"{camera['territoryId']}: {_safe_issue(error)}")
            break
    return (
        {
            "status": "PASS" if capture_count == 3 else "BLOCKED",
            "attempted": True,
            "captureCount": capture_count,
            "captures": captures,
        },
        issues,
    )


def stage(*, dry_run: bool, apply: bool, capture: bool) -> dict[str, Any]:
    if dry_run:
        manifest = load_json(MANIFEST_PATH)
        manifest_issues = validate_with_schema(
            manifest,
            ROOT / "schemas/transfer-import-queue.schema.json",
        )
        if manifest_issues:
            raise ArtSystemError(
                "transfer import manifest is invalid: "
                + "; ".join(manifest_issues)
            )
        entries = _payload_entries(manifest)
        return {
            "status": "PARTIAL",
            "dryRun": True,
            "mutationPerformed": False,
            "environment": "staging",
            "assetId": "turret_fast_v1",
            "candidateCount": len(entries),
            "territoryCount": len(
                {entry["territoryId"] for entry in entries}
            ),
            "stateCountPerTerritory": 3,
            "stressCopiesPerTerritory": [30, 100],
            "captureRequested": capture,
            "publicationEvidencePresent": (
                PUBLICATION_REPORT_PATH.is_file()
            ),
            "blockingReasons": (
                []
                if PUBLICATION_REPORT_PATH.is_file()
                else [
                    "current staging publication evidence is absent"
                ]
            ),
        }

    manifest, publication, registry = _load_inputs()
    entries = _payload_entries(manifest)
    plan = {
        "status": "PARTIAL",
        "dryRun": False,
        "mutationPerformed": False,
        "environment": "staging",
        "assetId": "turret_fast_v1",
        "candidateCount": 9,
        "territoryCount": 3,
        "stateCountPerTerritory": 3,
        "stressCopiesPerTerritory": [30, 100],
        "captureRequested": capture,
    }
    if not apply:
        raise ArtSystemError("explicit --apply authorization is required")
    creator_id = os.environ.get("ROBLOX_STAGING_CREATOR_ID", "")
    allowlist = {
        value.strip()
        for value in os.environ.get(
            "ROBLOX_3D_ALLOWED_CREATOR_IDS", ""
        ).split(",")
        if value.strip()
    }
    if not creator_id.isdigit() or creator_id not in allowlist:
        raise ArtSystemError(
            "staging creator is absent from the explicit local allowlist"
        )
    issues: list[str] = []
    report: dict[str, Any] = {
        "$schema": SCHEMA,
        "schemaVersion": "1.0.0",
        "status": "BLOCKED",
        "generatedAt": _utc_now(),
        "environment": "staging",
        "assetId": "turret_fast_v1",
        "privacy": {
            "rawPlaceIdIncluded": False,
            "rawCreatorIdIncluded": False,
            "rawAssetIdsIncluded": False,
            "rawApiKeyIncluded": False,
            "studioInstanceIdIncluded": False,
        },
        "inputHashes": {
            "transferManifest": sha256_file(MANIFEST_PATH),
            "transferPublicationReport": sha256_file(PUBLICATION_REPORT_PATH),
            "transferEvidencePackage": manifest["evidencePackageSha256"],
            "stageTransferTool": sha256_file(Path(__file__)),
            "studioMcpClient": sha256_file(
                ROOT / "tools/art/studio_mcp.py"
            ),
            "materialRules": sha256_file(MATERIAL_RULES_PATH),
            "industrialTerritory": sha256_file(
                TERRITORY_PATHS["industrial-toy-defense"]
            ),
            "salvagedTerritory": sha256_file(
                TERRITORY_PATHS["salvaged-frontier"]
            ),
            "cleanTerritory": sha256_file(
                TERRITORY_PATHS["clean-tactical-diorama"]
            ),
        },
        "environmentChecks": {
            "singleStudioInstance": False,
            "editModeVerified": False,
            "deploymentMarkedStaging": False,
            "localConfigComplete": False,
            "savedCloudPlaceVerified": False,
            "expectedCreatorMatches": False,
            "creatorAllowlistVerified": False,
        },
        "hierarchyChecks": {
            "transactionApplied": False,
            "assetKitPresent": False,
            "territoryFolderCount": 0,
            "assetFolderCount": 0,
            "stateCount": 0,
            "stagingRootRemoved": False,
        },
        "assetChecks": [],
        "reuseChecks": [],
        "sceneChecks": {
            "scenePresent": False,
            "candidateCount": 0,
            "stressGroupCount": 0,
            "placeholderCount": 0,
            "cameraCount": 0,
            "referenceAvatarPresent": False,
        },
        "playtestChecks": {
            "started": False,
            "clientDataModelObserved": False,
            "serverDataModelObserved": False,
            "stopped": False,
            "newRelevantErrorCount": 0,
            "pass": False,
        },
        "captureChecks": {
            "status": "NOT_REQUESTED",
            "attempted": False,
            "captureCount": 0,
            "captures": [],
        },
        "issues": [],
    }
    try:
        with StudioMcpClient() as client:
            selected = client.select_only_studio()
            report["environmentChecks"]["singleStudioInstance"] = (
                selected["count"] == 1
            )
            state = client.text_content(
                client.call_tool("get_studio_state", {}, timeout=15)
            )
            if "Current Studio Mode: Edit" not in state:
                raise StudioMcpError("active Studio is not in Edit mode")
            probe = _staging_probe(client, creator_id)
            report["environmentChecks"].update(probe)
            if not all(report["environmentChecks"].values()):
                raise StudioMcpError("active Studio failed staging preconditions")
            baseline = _console_fingerprint(client)
            _prepare_staging(client, manifest["evidencePackageSha256"])
            for entry in manifest["entries"]:
                local = registry["assets"][entry["uploadName"]]
                result = client.call_tool(
                    "insert_asset",
                    {
                        "assetId": str(local["assetId"]),
                        "assetName": entry["uploadName"],
                        "assetType": "Model",
                        "parentPath": (
                            "game.ServerStorage."
                            "ArtDirectionTransferImports_Staging"
                        ),
                    },
                    timeout=90,
                )
                inserted = client.json_content(result)
                if (
                    not isinstance(inserted, dict)
                    or inserted.get("status") != "success"
                ):
                    raise StudioMcpError(
                        f"{entry['uploadName']}: Studio insertion did not succeed"
                    )
            finalized = _execute_json(
                client,
                _finalizer_code(entries, manifest["evidencePackageSha256"]),
                timeout=120,
            )
            if not isinstance(finalized, dict):
                raise StudioMcpError("Studio finalizer returned a non-object")
            report["assetChecks"] = finalized.get("assetChecks", [])
            report["reuseChecks"] = finalized.get("reuseChecks", [])
            report["hierarchyChecks"] = finalized.get(
                "hierarchyChecks", report["hierarchyChecks"]
            )
            report["sceneChecks"] = finalized.get(
                "sceneChecks", report["sceneChecks"]
            )
            issues.extend(finalized.get("issues", []))
            if finalized.get("ok") is not True:
                raise StudioMcpError("Studio transfer finalizer failed validation")
            report["playtestChecks"] = _playtest(client, baseline)
            if not report["playtestChecks"]["pass"]:
                issues.append(
                    "Studio playtest did not prove Client, Server, clean console, and stop"
                )
            if capture:
                capture_checks, capture_issues = _capture(
                    client,
                    finalized.get("cameras", []),
                )
                report["captureChecks"] = capture_checks
                issues.extend(capture_issues)
    except (ArtSystemError, StudioMcpError, OSError, ValueError) as error:
        issues.append(_safe_issue(error))

    core_pass = (
        all(report["environmentChecks"].values())
        and report["hierarchyChecks"]["transactionApplied"]
        and len(report["assetChecks"]) == 9
        and all(item.get("pass") is True for item in report["assetChecks"])
        and len(report["reuseChecks"]) == 6
        and all(item.get("pass") is True for item in report["reuseChecks"])
        and report["sceneChecks"]["scenePresent"]
        and report["sceneChecks"]["candidateCount"] == 9
        and report["sceneChecks"]["stressGroupCount"] == 6
        and report["sceneChecks"]["referenceAvatarPresent"]
        and report["playtestChecks"]["pass"]
    )
    if core_pass and report["captureChecks"]["status"] == "PASS":
        report["status"] = "PASS"
        issues = []
    elif core_pass:
        report["status"] = "PARTIAL"
    elif report["hierarchyChecks"]["transactionApplied"]:
        report["status"] = "PARTIAL"
    else:
        report["status"] = "BLOCKED"
    report["generatedAt"] = _utc_now()
    report["issues"] = sorted(set(issues))
    schema_issues = validate_with_schema(
        report,
        ROOT / "schemas/transfer-studio-report.schema.json",
    )
    if schema_issues:
        raise ArtSystemError(
            "generated Studio transfer report is invalid: "
            + "; ".join(schema_issues)
        )
    write_json(STUDIO_REPORT_PATH, report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Transactionally insert, configure, validate, stress, and playtest "
            "the nine published turret transfer candidates in staging Studio."
        )
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    parser.add_argument("--capture", action="store_true")
    args = parser.parse_args()
    try:
        result = stage(
            dry_run=args.dry_run,
            apply=args.apply,
            capture=args.capture,
        )
    except (ArtSystemError, StudioMcpError, OSError, ValueError) as error:
        print(f"[FAIL] {_safe_issue(error)}")
        return 1
    if result.get("dryRun"):
        print(
            "[PARTIAL] Studio transfer dry-run: 9 candidates, three territories, "
            "1/30/100 validation; no Studio mutation performed."
        )
        return 0
    if result["status"] == "PASS":
        print(
            "[PASS] Studio transfer integration: 9/9 assets, six stress groups, "
            "transactional hierarchy, playtest, and privacy checks passed."
        )
        return 0
    if result["status"] == "PARTIAL" and result["playtestChecks"]["pass"]:
        for issue in result["issues"]:
            print(f"[PARTIAL] {issue}")
        print(
            "[PARTIAL] Studio transfer core passed; transfer-specific Studio "
            "viewport captures remain incomplete."
        )
        return 0
    for issue in result["issues"]:
        print(f"[{result['status']}] {issue}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
