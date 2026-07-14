Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repositoryRoot = Split-Path -Parent $PSScriptRoot
$rokitCommand = Get-Command rokit -ErrorAction SilentlyContinue
$rokitPath = if ($rokitCommand) { $rokitCommand.Source } else { $null }

if (-not $rokitPath -and $env:OS -eq "Windows_NT") {
    $candidate = Join-Path $env:USERPROFILE ".rokit\bin\rokit.exe"
    if (Test-Path -LiteralPath $candidate) {
        $rokitPath = (Resolve-Path -LiteralPath $candidate).Path
    }
}

if (-not $rokitPath) {
    throw "Rokit is not installed. Follow docs/TOOLING.md, then rerun this script."
}

Push-Location $repositoryRoot
try {
    . (Join-Path $PSScriptRoot "Resolve-RokitTool.ps1")

    $expectedVersions = [ordered]@{
        "stylua" = "2.5.2"
        "selene" = "0.31.0"
        "luau-lsp" = "1.68.1"
    }

    $missingTools = @($expectedVersions.Keys | Where-Object {
        try {
            Resolve-RokitTool -Alias $_ -RepositoryRoot $repositoryRoot | Out-Null
            return $false
        }
        catch {
            return $true
        }
    })

    if ($missingTools.Count -gt 0) {
        Write-Output "Installing missing Rokit tools: $($missingTools -join ', ')"
        & $rokitPath install
        if ($LASTEXITCODE -ne 0) {
            throw "rokit install failed with exit code $LASTEXITCODE. Trust the reviewed repositories listed in docs/TOOLING.md, then retry."
        }
    }

    foreach ($alias in $expectedVersions.Keys) {
        $tool = Resolve-RokitTool -Alias $alias -RepositoryRoot $repositoryRoot
        $versionOutput = & $tool --version
        $versionExitCode = $LASTEXITCODE
        $actualVersion = ($versionOutput | Select-Object -First 1) -join ""
        if ($versionExitCode -ne 0 -or $actualVersion -notmatch [Regex]::Escape($expectedVersions[$alias])) {
            throw "Unexpected $alias version: '$actualVersion' (expected $($expectedVersions[$alias]))"
        }
        Write-Output "PASS $alias $actualVersion"
    }
}
finally {
    Pop-Location
}
