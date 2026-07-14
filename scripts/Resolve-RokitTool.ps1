Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-RokitTool {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [ValidateNotNullOrEmpty()]
        [string] $Alias,

        [string] $RepositoryRoot = (Split-Path -Parent $PSScriptRoot)
    )

    $manifestPath = Join-Path $RepositoryRoot "rokit.toml"
    if (-not (Test-Path -LiteralPath $manifestPath)) {
        throw "Missing Rokit manifest: $manifestPath"
    }

    $escapedAlias = [Regex]::Escape($Alias)
    $pattern = '^\s*{0}\s*=\s*"([^"]+)@([^"]+)"\s*$' -f $escapedAlias
    $match = Select-String -LiteralPath $manifestPath -Pattern $pattern | Select-Object -First 1
    if (-not $match) {
        throw "Tool '$Alias' is not pinned in $manifestPath"
    }

    $repository = $match.Matches[0].Groups[1].Value
    $version = $match.Matches[0].Groups[2].Value
    $repositoryParts = $repository -split "/", 2
    if ($repositoryParts.Count -ne 2) {
        throw "Invalid Rokit tool specification for '$Alias': $repository@$version"
    }

    if ($env:OS -eq "Windows_NT") {
        $rokitRoot = Join-Path $env:USERPROFILE ".rokit"
        $candidate = Join-Path $rokitRoot (
            "tool-storage\{0}\{1}\{2}\{3}.exe" -f
                $repositoryParts[0].ToLowerInvariant(),
                $repositoryParts[1].ToLowerInvariant(),
                $version,
                $Alias
        )

        if (Test-Path -LiteralPath $candidate) {
            return (Resolve-Path -LiteralPath $candidate).Path
        }
    }

    $command = Get-Command $Alias -ErrorAction SilentlyContinue
    if ($command) {
        return $command.Source
    }

    throw "Rokit tool '$Alias' is not installed. Run scripts/bootstrap.ps1 first."
}
