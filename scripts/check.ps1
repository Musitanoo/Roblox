Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repositoryRoot = Split-Path -Parent $PSScriptRoot
. (Join-Path $PSScriptRoot "Resolve-RokitTool.ps1")

Push-Location $repositoryRoot
try {
    Get-Content -Raw -LiteralPath ".luaurc" | ConvertFrom-Json | Out-Null
    Get-Content -Raw -LiteralPath ".vscode\extensions.json" | ConvertFrom-Json | Out-Null
    Get-Content -Raw -LiteralPath ".vscode\settings.json" | ConvertFrom-Json | Out-Null
    Get-Content -Raw -LiteralPath "studio\DefenseLoop-0.1-baseline.manifest.json" | ConvertFrom-Json | Out-Null
    Write-Output "PASS configuration JSON"

    $stylua = Resolve-RokitTool -Alias "stylua" -RepositoryRoot $repositoryRoot
    $selene = Resolve-RokitTool -Alias "selene" -RepositoryRoot $repositoryRoot
    $luauLsp = Resolve-RokitTool -Alias "luau-lsp" -RepositoryRoot $repositoryRoot

    & $selene validate-config
    if ($LASTEXITCODE -ne 0) {
        throw "Selene configuration validation failed with exit code $LASTEXITCODE"
    }
    Write-Output "PASS Selene configuration"

    $sourceRoots = @("data/src", "tests") | Where-Object { Test-Path -LiteralPath $_ }
    $sources = @($sourceRoots | ForEach-Object {
        Get-ChildItem -LiteralPath $_ -Recurse -File | Where-Object {
            $_.Extension -in ".lua", ".luau"
        }
    })

    if ($sources.Count -eq 0) {
        Write-Output "SKIP Luau checks: no source files found."
        exit 0
    }

    & $stylua --config-path "stylua.toml" --verify --check @($sources.FullName)
    if ($LASTEXITCODE -ne 0) {
        throw "StyLua check failed with exit code $LASTEXITCODE"
    }
    Write-Output "PASS StyLua"

    & $selene @($sourceRoots)
    if ($LASTEXITCODE -ne 0) {
        throw "Selene failed with exit code $LASTEXITCODE"
    }
    Write-Output "PASS Selene"

    $robloxDefinitions = Join-Path $repositoryRoot "tools\luau-lsp\globalTypes.d.luau"
    if (-not (Test-Path -LiteralPath $robloxDefinitions)) {
        throw "Missing pinned Roblox type definitions: $robloxDefinitions"
    }

    & $luauLsp analyze --platform roblox --definitions "@roblox=$robloxDefinitions" @($sources.FullName)
    if ($LASTEXITCODE -ne 0) {
        throw "Luau LSP analysis failed with exit code $LASTEXITCODE"
    }
    Write-Output "PASS Luau LSP analysis"
}
finally {
    Pop-Location
}
