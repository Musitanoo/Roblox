Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repositoryRoot = Split-Path -Parent $PSScriptRoot
$manifestPath = Join-Path $repositoryRoot "studio\DefenseLoop-0.1-baseline.manifest.json"

if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
    throw "Missing Studio baseline manifest: $manifestPath"
}

$manifest = Get-Content -Raw -LiteralPath $manifestPath | ConvertFrom-Json
if ($manifest.schemaVersion -ne 1 -or $manifest.slice -ne "Defense Loop 0.1") {
    throw "Unsupported Studio baseline manifest identity."
}

$snapshotPath = Join-Path $repositoryRoot ($manifest.localSnapshot.relativePath -replace "/", "\")
if (-not (Test-Path -LiteralPath $snapshotPath -PathType Leaf)) {
    throw "Missing ignored local Studio snapshot: $snapshotPath"
}

$snapshot = Get-Item -LiteralPath $snapshotPath
if ($snapshot.Length -ne [long]$manifest.localSnapshot.length) {
    throw "Studio snapshot length mismatch: expected $($manifest.localSnapshot.length), got $($snapshot.Length)."
}

$actualHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $snapshotPath).Hash
if ($actualHash -ne $manifest.localSnapshot.sha256) {
    throw "Studio snapshot SHA-256 mismatch: expected $($manifest.localSnapshot.sha256), got $actualHash."
}

$requiredPads = @($manifest.prototype.buildPads)
$requiredLaneNodes = @($manifest.prototype.lane)
$requiredTemplates = @($manifest.templates)
if ($requiredPads.Count -ne 4 -or $requiredLaneNodes.Count -ne 4 -or $requiredTemplates.Count -ne 3) {
    throw "Studio baseline manifest has an unexpected critical-instance count."
}

Write-Output "PASS Studio baseline identity"
Write-Output "PASS Studio baseline snapshot length"
Write-Output "PASS Studio baseline snapshot SHA-256"
Write-Output "PASS Studio baseline critical inventory"
