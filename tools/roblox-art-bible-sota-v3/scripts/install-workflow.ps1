[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$TargetRepo,
    [string]$PythonPath,
    [switch]$Replace,
    [switch]$SkipBootstrap,
    [switch]$SkipLuauValidation
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$SourceRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$TargetRoot = (Resolve-Path -LiteralPath $TargetRepo).Path
$ManifestPath = Join-Path $SourceRoot 'PACKAGE_MANIFEST.json'
$WorkflowName = 'roblox-art-bible-sota-v3'
$TargetTools = Join-Path $TargetRoot 'tools'
$Destination = Join-Path $TargetTools $WorkflowName
$Stage = Join-Path $TargetTools ('.' + $WorkflowName + '.install-' + [guid]::NewGuid().ToString('N'))
$SkillSourceRelative = '.agents/skills/roblox-3d-asset'
$SkillDestination = Join-Path $TargetRoot $SkillSourceRelative
$WrapperDestination = Join-Path $TargetRoot 'scripts/art-direction.ps1'
$PipelineSourceRelative = 'tools/roblox-3d-asset'
$PipelineDestination = Join-Path $TargetRoot $PipelineSourceRelative
$AssetContractSourceRelative = 'assets-3d/defense-barricade-small/asset.json'
$AssetContractDestination = Join-Path $TargetRoot $AssetContractSourceRelative
$PrecanonicalReferenceSourceRelative = 'assets-3d/defense-barricade-small/precanonical/requests/defense-barricade-web-001'
$PrecanonicalReferenceDestination = Join-Path $TargetRoot $PrecanonicalReferenceSourceRelative
$Stamp = [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ')

function Assert-UnderRoot([string]$Path, [string]$Root, [string]$Label) {
    $candidate = [System.IO.Path]::GetFullPath($Path)
    $boundary = [System.IO.Path]::GetFullPath($Root).TrimEnd('\') + '\'
    if (-not $candidate.StartsWith($boundary, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "$Label escapes the target root: $candidate"
    }
}

function Invoke-Checked([string]$Executable, [string[]]$Arguments, [string]$Label) {
    Write-Host "> $Label"
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$Label failed with exit code $LASTEXITCODE"
    }
}

function Resolve-InstallerPython {
    $candidates = [System.Collections.Generic.List[string]]::new()
    if ($PythonPath) { $candidates.Add($PythonPath) }
    if ($env:ART_PYTHON) { $candidates.Add($env:ART_PYTHON) }
    $sourcePython = if ($env:OS -eq 'Windows_NT') {
        Join-Path $SourceRoot '.venv\Scripts\python.exe'
    }
    else {
        Join-Path $SourceRoot '.venv/bin/python'
    }
    if (Test-Path -LiteralPath $sourcePython -PathType Leaf) {
        $candidates.Add($sourcePython)
    }
    foreach ($name in @('python3', 'python', 'py')) {
        $command = Get-Command $name -ErrorAction SilentlyContinue
        if ($command) { $candidates.Add($command.Source) }
    }
    foreach ($candidate in $candidates | Select-Object -Unique) {
        try {
            & $candidate --version *> $null
            if ($LASTEXITCODE -eq 0) {
                return (Resolve-Path -LiteralPath $candidate).Path
            }
        }
        catch {
            continue
        }
    }
    throw 'Python 3 was not found for staged bootstrap. Use -PythonPath or ART_PYTHON.'
}

if (-not (Test-Path -LiteralPath (Join-Path $TargetRoot 'AGENTS.md') -PathType Leaf)) {
    throw "TargetRepo is not the expected Roblox repository: AGENTS.md is missing."
}
if (-not (Test-Path -LiteralPath $ManifestPath -PathType Leaf)) {
    throw "PACKAGE_MANIFEST.json is missing. Build the release package before installation."
}
Assert-UnderRoot $Destination $TargetRoot 'Workflow destination'
Assert-UnderRoot $Stage $TargetRoot 'Workflow staging directory'
Assert-UnderRoot $SkillDestination $TargetRoot 'Skill destination'
Assert-UnderRoot $WrapperDestination $TargetRoot 'Wrapper destination'
Assert-UnderRoot $PipelineDestination $TargetRoot 'Per-asset pipeline destination'
Assert-UnderRoot $AssetContractDestination $TargetRoot 'Asset contract destination'
Assert-UnderRoot $PrecanonicalReferenceDestination $TargetRoot 'Precanonical reference destination'

if ((Test-Path -LiteralPath $Destination) -and -not $Replace) {
    throw "Workflow already exists at $Destination. Re-run with -Replace for a backed-up replacement."
}
if ((Test-Path -LiteralPath $SkillDestination) -and -not $Replace) {
    throw "Skill already exists at $SkillDestination. Re-run with -Replace for a backed-up replacement."
}
if ((Test-Path -LiteralPath $WrapperDestination) -and -not $Replace) {
    throw "Wrapper already exists at $WrapperDestination. Re-run with -Replace for a backed-up replacement."
}
if ((Test-Path -LiteralPath $PipelineDestination) -and -not $Replace) {
    throw "Per-asset pipeline already exists at $PipelineDestination. Re-run with -Replace for a backed-up replacement."
}
if ((Test-Path -LiteralPath $AssetContractDestination) -and -not $Replace) {
    throw "Asset contract already exists at $AssetContractDestination. Re-run with -Replace for a backed-up replacement."
}

$Manifest = Get-Content -LiteralPath $ManifestPath -Raw | ConvertFrom-Json
New-Item -ItemType Directory -Force -Path $Stage | Out-Null
try {
    foreach ($entry in $Manifest.files) {
        $relative = [string]$entry.path
        $source = Join-Path $SourceRoot ($relative -replace '/', '\')
        $destinationFile = Join-Path $Stage ($relative -replace '/', '\')
        Assert-UnderRoot $destinationFile $Stage 'Manifest member'
        if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
            throw "Manifest source is missing: $relative"
        }
        $sourceHash = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($sourceHash -ne [string]$entry.sha256) {
            throw "Manifest source hash mismatch: $relative"
        }
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $destinationFile) | Out-Null
        Copy-Item -LiteralPath $source -Destination $destinationFile
        $copiedHash = (Get-FileHash -LiteralPath $destinationFile -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($copiedHash -ne $sourceHash) {
            throw "Copied file hash mismatch: $relative"
        }
    }
    Copy-Item -LiteralPath $ManifestPath -Destination (Join-Path $Stage 'PACKAGE_MANIFEST.json')

    $StageRunner = Join-Path $Stage 'scripts/art-direction.ps1'
    if (-not $SkipBootstrap) {
        $InstallerPython = Resolve-InstallerPython
        Invoke-Checked 'powershell' @(
            '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $StageRunner,
            'bootstrap', '-PythonPath', $InstallerPython
        ) 'Bootstrap staged workflow'
    }
    Invoke-Checked 'powershell' @(
        '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $StageRunner, 'validate'
    ) 'Validate staged workflow'
    Invoke-Checked 'powershell' @(
        '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $StageRunner, 'test'
    ) 'Test staged workflow'
    if (-not $SkipLuauValidation) {
        Invoke-Checked 'powershell' @(
            '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $StageRunner, 'validate-luau'
        ) 'Validate staged Luau'
    }

    $PreservedHumanEvidence = $false
    $ExistingHumanEvidence = Join-Path $Destination 'evidence/human'
    if (Test-Path -LiteralPath $ExistingHumanEvidence -PathType Container) {
        $localEntries = @(
            Get-ChildItem -LiteralPath $ExistingHumanEvidence -Force |
                Where-Object { $_.Name -ne '.gitkeep' }
        )
        if ($localEntries.Count -gt 0) {
            $StagedHumanEvidence = Join-Path $Stage 'evidence/human'
            New-Item -ItemType Directory -Force -Path $StagedHumanEvidence | Out-Null
            foreach ($entry in $localEntries) {
                Copy-Item -LiteralPath $entry.FullName -Destination $StagedHumanEvidence -Recurse -Force
            }
            $PreservedHumanEvidence = $true
            Write-Host "[PASS] Preserved local human-study evidence in staged replacement"
        }
    }

    $WorkflowBackup = $null
    $SkillBackup = $null
    $WrapperBackup = $null
    $PipelineBackup = $null
    $AssetContractBackup = $null
    $PrecanonicalReferenceBackup = $null
    $PrecanonicalReferencePreserved = Test-Path -LiteralPath $PrecanonicalReferenceDestination
    $WorkflowReplacedInPlace = $false
    if (Test-Path -LiteralPath $Destination) {
        $WorkflowBackup = "$Destination.backup-$Stamp"
        try {
            Move-Item -LiteralPath $Destination -Destination $WorkflowBackup
        }
        catch [System.IO.IOException] {
            Write-Warning (
                "Atomic workflow-directory move is blocked by Windows. " +
                "Creating a full backup and using manifest-verified in-place replacement."
            )
            Copy-Item -LiteralPath $Destination -Destination $WorkflowBackup -Recurse
            $WorkflowReplacedInPlace = $true
        }
    }
    if (Test-Path -LiteralPath $SkillDestination) {
        $SkillBackup = "$SkillDestination.backup-$Stamp"
        Move-Item -LiteralPath $SkillDestination -Destination $SkillBackup
    }
    if (Test-Path -LiteralPath $WrapperDestination) {
        $WrapperBackup = "$WrapperDestination.backup-$Stamp"
        Move-Item -LiteralPath $WrapperDestination -Destination $WrapperBackup
    }
    if (Test-Path -LiteralPath $PipelineDestination) {
        $PipelineBackup = "$PipelineDestination.backup-$Stamp"
        Move-Item -LiteralPath $PipelineDestination -Destination $PipelineBackup
    }
    if (Test-Path -LiteralPath $AssetContractDestination) {
        $AssetContractBackup = "$AssetContractDestination.backup-$Stamp"
        Move-Item -LiteralPath $AssetContractDestination -Destination $AssetContractBackup
    }
    if ($WorkflowReplacedInPlace) {
        foreach ($entry in $Manifest.files) {
            $relative = [string]$entry.path
            $source = Join-Path $Stage ($relative -replace '/', '\')
            $destinationFile = Join-Path $Destination ($relative -replace '/', '\')
            Assert-UnderRoot $destinationFile $Destination 'In-place manifest member'
            New-Item -ItemType Directory -Force -Path (Split-Path -Parent $destinationFile) | Out-Null
            Copy-Item -LiteralPath $source -Destination $destinationFile -Force
            $installedHash = (Get-FileHash -LiteralPath $destinationFile -Algorithm SHA256).Hash.ToLowerInvariant()
            if ($installedHash -ne [string]$entry.sha256) {
                throw "In-place installed file hash mismatch: $relative"
            }
        }
        Copy-Item -LiteralPath (Join-Path $Stage 'PACKAGE_MANIFEST.json') -Destination (Join-Path $Destination 'PACKAGE_MANIFEST.json') -Force
    }
    else {
        Move-Item -LiteralPath $Stage -Destination $Destination
    }
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $SkillDestination) | Out-Null
    Copy-Item -LiteralPath (Join-Path $Destination $SkillSourceRelative) -Destination $SkillDestination -Recurse
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $WrapperDestination) | Out-Null
    $wrapper = @'
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]] $WorkflowArguments
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$repositoryRoot = Split-Path -Parent $PSScriptRoot
$entrypoint = Join-Path $repositoryRoot 'tools/roblox-art-bible-sota-v3/scripts/art-direction.ps1'
if (-not (Test-Path -LiteralPath $entrypoint -PathType Leaf)) {
    throw "Missing installed art-direction workflow: $entrypoint"
}
& powershell -NoProfile -ExecutionPolicy Bypass -File $entrypoint @WorkflowArguments
exit $LASTEXITCODE
'@
    [System.IO.File]::WriteAllText(
        $WrapperDestination,
        $wrapper,
        [System.Text.UTF8Encoding]::new($false)
    )
    Copy-Item -LiteralPath (Join-Path $Destination $PipelineSourceRelative) -Destination $PipelineDestination -Recurse
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $AssetContractDestination) | Out-Null
    Copy-Item -LiteralPath (Join-Path $Destination $AssetContractSourceRelative) -Destination $AssetContractDestination
    if (-not $PrecanonicalReferencePreserved) {
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $PrecanonicalReferenceDestination) | Out-Null
        Copy-Item -LiteralPath (Join-Path $Destination $PrecanonicalReferenceSourceRelative) -Destination $PrecanonicalReferenceDestination -Recurse
    }

    $Receipt = @{
        schemaVersion = '1.2.0'
        installedAt = [DateTime]::UtcNow.ToString('o')
        artifact = $Manifest.artifact
        artifactVersion = $Manifest.artifactVersion
        treeSha256 = $Manifest.treeSha256
        workflowPath = 'tools/roblox-art-bible-sota-v3'
        skillPath = '.agents/skills/roblox-3d-asset'
        wrapperPath = 'scripts/art-direction.ps1'
        perAssetPipelinePath = 'tools/roblox-3d-asset'
        referenceAssetContractPath = 'assets-3d/defense-barricade-small/asset.json'
        precanonicalReferencePath = 'assets-3d/defense-barricade-small/precanonical/requests/defense-barricade-web-001'
        precanonicalReferencePreserved = $PrecanonicalReferencePreserved
        localHumanEvidencePreserved = $PreservedHumanEvidence
        workflowReplacedInPlace = $WorkflowReplacedInPlace
        backups = @{
            workflow = $WorkflowBackup
            skill = $SkillBackup
            wrapper = $WrapperBackup
            perAssetPipeline = $PipelineBackup
            referenceAssetContract = $AssetContractBackup
            precanonicalReference = $PrecanonicalReferenceBackup
        }
    }
    $ReceiptPath = Join-Path $TargetTools 'roblox-art-bible-sota-v3.install.json'
    $Receipt | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $ReceiptPath -Encoding UTF8
    Write-Host "[PASS] Workflow installed at $Destination"
    Write-Host "[PASS] Skill installed at $SkillDestination"
    Write-Host "[PASS] Wrapper installed at $WrapperDestination"
    Write-Host "[PASS] Per-asset pipeline installed at $PipelineDestination"
    Write-Host "[PASS] Canon-bound reference contract installed at $AssetContractDestination"
    if ($PrecanonicalReferencePreserved) {
        Write-Host "[PASS] Existing precanonical request and bound human evidence preserved at $PrecanonicalReferenceDestination"
    }
    else {
        Write-Host "[PASS] Precanonical reference request installed at $PrecanonicalReferenceDestination"
    }
}
catch {
    if (Test-Path -LiteralPath $Stage) {
        Write-Warning "Staged installation remains for diagnosis: $Stage"
    }
    throw
}
