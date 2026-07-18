param(
    [switch] $Check
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repositoryRoot = Split-Path -Parent $PSScriptRoot
. (Join-Path $PSScriptRoot "Resolve-RokitTool.ps1")
$stylua = Resolve-RokitTool -Alias "stylua" -RepositoryRoot $repositoryRoot

$targets = @()
foreach ($relativePath in @("data/src", "tests")) {
    $path = Join-Path $repositoryRoot $relativePath
    if (Test-Path -LiteralPath $path) {
        $targets += $path
    }
}

$sources = @($targets | ForEach-Object {
    Get-ChildItem -LiteralPath $_ -Recurse -File | Where-Object {
        $_.Extension -in ".lua", ".luau"
    }
})

if ($sources.Count -eq 0) {
    Write-Output "SKIP StyLua: no Luau source files found."
    exit 0
}

$arguments = @("--config-path", (Join-Path $repositoryRoot "stylua.toml"), "--verify")
if ($Check) {
    $arguments += "--check"
}
$arguments += $sources.FullName

& $stylua @arguments
exit $LASTEXITCODE
