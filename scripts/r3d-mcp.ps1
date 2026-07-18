param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repositoryRoot = Split-Path -Parent $PSScriptRoot
$entrypoint = Join-Path $repositoryRoot "tools\roblox-3d-asset\r3d.py"
$candidates = @()
if ($env:PYTHON_EXE) {
    $candidates += $env:PYTHON_EXE
}
$candidates += (Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe")
$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
if ($pythonCommand) {
    $candidates += $pythonCommand.Source
}
$python = $candidates | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1
if (-not $python) {
    throw "Python 3 was not found. Set PYTHON_EXE to an explicit executable path."
}

# This server can launch Blender. Strip inherited credentials before the
# long-lived MCP process starts; executable-discovery variables remain intact.
$sensitiveNamePattern = (
    '^(ROBLOX_OPEN_CLOUD_API_KEY|ROBLOX_STAGING_CREATOR_ID|' +
    'ROBLOX_3D_ALLOWED_CREATOR_IDS|ROBLOX_SECURITY|OPENAI_API_KEY|' +
    'GITHUB_TOKEN|GH_TOKEN|AWS_ACCESS_KEY_ID|AWS_SECRET_ACCESS_KEY|' +
    'AWS_SESSION_TOKEN|AZURE_CLIENT_SECRET|GOOGLE_APPLICATION_CREDENTIALS|' +
    'HF_TOKEN|HUGGINGFACE_HUB_TOKEN|NPM_TOKEN)$|' +
    '(_API_KEY|_COOKIE|_CREDENTIAL|_CREDENTIALS|_PASSWORD|' +
    '_PRIVATE_KEY|_SECRET|_TOKEN)$'
)
Get-ChildItem Env: |
    Where-Object { $_.Name -match $sensitiveNamePattern } |
    ForEach-Object {
        [Environment]::SetEnvironmentVariable($_.Name, $null, 'Process')
    }

Push-Location $repositoryRoot
try {
    & $python $entrypoint blender-mcp-server --repo $repositoryRoot
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
