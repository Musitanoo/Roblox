param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]] $PipelineArguments
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repositoryRoot = Split-Path -Parent $PSScriptRoot
$entrypoint = Join-Path $repositoryRoot "tools\roblox-3d-asset\r3d.py"

$candidates = @()
if ($env:PYTHON_EXE) {
    $candidates += $env:PYTHON_EXE
}
$bundledRuntime = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
$candidates += $bundledRuntime
$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
if ($pythonCommand) {
    $candidates += $pythonCommand.Source
}

$python = $candidates | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1
if (-not $python) {
    throw "Python 3 was not found. Set PYTHON_EXE to an explicit executable path."
}
if (-not (Test-Path -LiteralPath $entrypoint -PathType Leaf)) {
    throw "Missing pipeline entrypoint: $entrypoint"
}

if ($env:OS -eq "Windows_NT" -and -not (Get-Command git -ErrorAction SilentlyContinue)) {
    $gitCommandDirectory = Join-Path $env:ProgramFiles "Git\cmd"
    $gitExecutable = Join-Path $gitCommandDirectory "git.exe"
    if (Test-Path -LiteralPath $gitExecutable -PathType Leaf) {
        $env:Path = "$gitCommandDirectory;$env:Path"
    }
}

$cloudEnvironmentNames = @(
    "ROBLOX_OPEN_CLOUD_API_KEY",
    "ROBLOX_STAGING_CREATOR_ID",
    "ROBLOX_3D_ALLOWED_CREATOR_IDS"
)
$pipelineCommand = if (@($PipelineArguments).Count -gt 0) {
    [string]$PipelineArguments[0]
}
else {
    ""
}
$needsCloudEnvironment = $pipelineCommand -in @("doctor", "publish")
foreach ($name in $cloudEnvironmentNames) {
    if (-not $needsCloudEnvironment) {
        [Environment]::SetEnvironmentVariable($name, $null, "Process")
        continue
    }
    if ((Test-Path "Env:$name") -or $env:OS -ne "Windows_NT") {
        continue
    }
    $value = [Environment]::GetEnvironmentVariable($name, "User")
    if ($value) {
        [Environment]::SetEnvironmentVariable($name, $value, "Process")
    }
}

Push-Location $repositoryRoot
try {
    & $python $entrypoint @PipelineArguments
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
