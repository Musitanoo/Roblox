<#
.SYNOPSIS
Shows or dispatches the installed Roblox art-direction workflow.

.DESCRIPTION
Use `help` or `--help` to display the observable command surface. Common
read-only commands include doctor, validate, validate-canons, validate-luau,
validate-transfer, and test. No workflow command is executed while help is
displayed. Help never executes a workflow command.

.EXAMPLE
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\art-direction.ps1 help

.EXAMPLE
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\art-direction.ps1 doctor
#>
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]] $WorkflowArguments
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-ArtDirectionHelp {
    @'
Roblox art-direction workflow

Usage:
  powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\art-direction.ps1 help
  powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\art-direction.ps1 <command> [options]

Read-only discovery and validation:
  doctor  validate  validate-canons  validate-luau  validate-transfer  test

Workflow groups:
  precanon-*  canons  lock-canon  build  workbench  transfer
  validate-studio  validate-simulator  validate-mobile
  prepare-study  seal-study  score  lock  package

Safety:
  Publication and Studio application remain dry-run unless their explicit
  confirmation/apply switches are supplied under current user authority.
  Help never executes a workflow command.
'@
}

$helpTokens = @('help', '--help', '-h')
if (
    $WorkflowArguments.Count -eq 1 -and
    $helpTokens -contains $WorkflowArguments[0]
) {
    Write-ArtDirectionHelp
    exit 0
}

$repositoryRoot = Split-Path -Parent $PSScriptRoot
$entrypoint = Join-Path $repositoryRoot 'tools/roblox-art-bible-sota-v3/scripts/art-direction.ps1'
if (-not (Test-Path -LiteralPath $entrypoint -PathType Leaf)) {
    throw "Missing installed art-direction workflow: $entrypoint"
}
& powershell -NoProfile -ExecutionPolicy Bypass -File $entrypoint @WorkflowArguments
exit $LASTEXITCODE
