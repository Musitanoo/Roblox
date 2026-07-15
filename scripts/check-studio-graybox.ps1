Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repositoryRoot = Split-Path -Parent $PSScriptRoot
$manifestPath = Join-Path $repositoryRoot "studio\DefenseLoop-0.2-graybox.manifest.json"

if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
    throw "Missing Studio graybox manifest: $manifestPath"
}

$manifest = Get-Content -Raw -LiteralPath $manifestPath | ConvertFrom-Json
if ($manifest.schemaVersion -ne 1 -or $manifest.slice -ne "Defense Loop 0.2") {
    throw "Unsupported Studio graybox manifest identity."
}

$snapshotPath = Join-Path $repositoryRoot ($manifest.localSnapshot.relativePath -replace "/", "\")
if (-not (Test-Path -LiteralPath $snapshotPath -PathType Leaf)) {
    throw "Missing ignored local Studio graybox snapshot: $snapshotPath"
}

$snapshot = Get-Item -LiteralPath $snapshotPath
if ($snapshot.Length -ne [long]$manifest.localSnapshot.length) {
    throw "Studio graybox snapshot length mismatch: expected $($manifest.localSnapshot.length), got $($snapshot.Length)."
}

$actualHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $snapshotPath).Hash
if ($actualHash -ne $manifest.localSnapshot.sha256) {
    throw "Studio graybox snapshot SHA-256 mismatch: expected $($manifest.localSnapshot.sha256), got $actualHash."
}

$laneNodes = @($manifest.workspaceDelta.lane02.nodes)
if ($laneNodes.Count -ne 4) {
    throw "Lane02 must contain exactly four direct navigation nodes."
}

foreach ($node in $laneNodes) {
    if ($node.nestedVisualParts -ne 5) {
        throw "$($node.name) must contain exactly five nested readability Parts."
    }
}

$brute = $manifest.templateDelta.brute
if ($brute.primaryPart -ne "Root" -or $brute.parts -ne 14 -or $brute.scripts -ne 0) {
    throw "Brute template structure does not match the approved graybox."
}

if ($manifest.readabilityEvidence.temporaryPreviewPresent -ne $false) {
    throw "The temporary Brute readability preview must not remain in the delivered Studio hierarchy."
}

Write-Output "PASS Studio graybox identity"
Write-Output "PASS Studio graybox snapshot length"
Write-Output "PASS Studio graybox snapshot SHA-256"
Write-Output "PASS Lane02 critical inventory"
Write-Output "PASS Brute primitive inventory"
Write-Output "PASS temporary preview cleanup"
