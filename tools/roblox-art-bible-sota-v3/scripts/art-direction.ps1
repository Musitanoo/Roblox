[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet('bootstrap', 'doctor', 'precanon-init', 'precanon-preflight', 'precanon-browser-doctor', 'precanon-handoff', 'precanon-operator', 'precanon-campaign-init', 'precanon-campaign-snapshot', 'precanon-campaign-fork', 'precanon-campaign-operator', 'precanon-import', 'precanon-review', 'precanon-status', 'canons', 'validate-canons', 'lock-canon', 'validate', 'generate', 'test', 'validate-luau', 'build', 'review', 'workbench', 'simulate-workflow', 'verify-blender', 'measure-visual', 'transfer', 'validate-transfer', 'publish-transfer', 'stage-transfer', 'bind-studio-captures', 'validate-studio', 'validate-simulator', 'validate-mobile', 'prepare-study', 'seal-study', 'evidence-index', 'score', 'lock', 'package')]
    [string]$Command = 'validate',

    [string]$PythonPath,
    [string]$BlenderPath,
    [string]$RokitBin,
    [string]$Territory,
    [ValidateSet('build-only', 'smoke', 'full')]
    [string]$RenderMode = 'smoke',
    [string]$Submissions,
    [string]$BlindMap,
    [string]$Decision,
    [string]$ScoringReport,
    [string]$EvidenceIndex,
    [string]$LockedBy,
    [string]$Asset,
    [string]$CanonEvidence,
    [string]$HumanReview,
    [string]$DecisionRecord,
    [string]$StudyRoot,
    [string]$EvidenceRoot,
    [string]$Output,
    [string]$Report,
    [string]$Request,
    [string]$Campaign,
    [string]$SourceCampaign,
    [string]$CampaignId = 'salvaged-frontier-states-v2',
    [string]$RestartTaskId,
    [string]$RevisionReason,
    [string]$Brief,
    [string]$RequestId,
    [ValidateSet('exploration', 'consolidation', 'precanonical_board', 'state_definition', 'correction')]
    [string]$PrecanonicalStage = 'exploration',
    [ValidateSet('codex_chrome', 'codex_iab')]
    [string]$BrowserAdapter = 'codex_chrome',
    [int]$MaximumWebGenerations = 4,
    [int]$Port = 0,
    [int]$IdleTimeoutMinutes = 120,
    [int]$MaxAttemptsPerTask = 3,
    [string]$Preflight,
    [string]$BrowserDoctor,
    [string]$Result,
    [string]$ResultId,
    [string[]]$Image,
    [ValidateSet('browser_download', 'manual_download')]
    [string]$DownloadMethod = 'browser_download',
    [string]$ModelName,
    [ValidateSet('REJECTED', 'REVISION_REQUIRED', 'PRECANONICAL_CANDIDATE', 'HUMAN_SELECTED')]
    [string]$ReviewDecision,
    [string]$Reviewer,
    [string]$Assessment,
    [string[]]$Preserve,
    [string[]]$Correct,
    [string[]]$ForbidNext,
    [string[]]$RevisionInstruction,
    [switch]$ReviewRenders,
    [switch]$Resume,
    [switch]$DryRun,
    [switch]$ConfirmPublish,
    [switch]$Open,
    [switch]$RequirePass,
    [switch]$RequireEligible,
    [switch]$RequireLockedCanons,
    [switch]$UseR3DDoctor,
    [switch]$NoHumanConfirmation,
    [switch]$AuthorizeAutomaticSubmission,
    [switch]$ModelNameUiConfirmed,
    [switch]$NoOpen,
    [switch]$Apply
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$Root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$ProjectRootCandidate = Split-Path -Parent (Split-Path -Parent $Root)
$ProjectRoot = if (
    Test-Path -LiteralPath (Join-Path $ProjectRootCandidate 'AGENTS.md') -PathType Leaf
) {
    (Resolve-Path -LiteralPath $ProjectRootCandidate).Path
}
else {
    $Root
}
$PythonSpec = $null
$BlenderExe = $null
$ExpectedBlenderVersion = '5.2.0'
$ExpectedRokitToolVersions = @{ stylua = '2.5.2'; selene = '0.31.0'; 'luau-lsp' = '1.68.1' }
$IsWindowsPlatform = ($env:OS -eq 'Windows_NT')
$IsMacOSPlatform = [System.Runtime.InteropServices.RuntimeInformation]::IsOSPlatform(
    [System.Runtime.InteropServices.OSPlatform]::OSX
)

function Write-Section([string]$Message) {
    Write-Host "`n=== $Message ===" -ForegroundColor Cyan
}

function Resolve-WorkflowPath([string]$Path, [bool]$ForOutput = $false) {
    if (-not $Path) { return $Path }
    if ([System.IO.Path]::IsPathRooted($Path)) {
        return [System.IO.Path]::GetFullPath($Path)
    }
    $normalized = ($Path -replace '/', '\').TrimStart('.', '\')
    $projectPrefixes = @(
        'assets-3d\',
        'tools\roblox-art-bible-sota-v3\',
        'plans\',
        'docs\'
    )
    $workflowPrefixes = @(
        'art\',
        'schemas\',
        'evidence\',
        'build\',
        'studio\'
    )
    foreach ($prefix in $projectPrefixes) {
        if ($normalized.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) {
            return [System.IO.Path]::GetFullPath((Join-Path $ProjectRoot $normalized))
        }
    }
    foreach ($prefix in $workflowPrefixes) {
        if ($normalized.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) {
            return [System.IO.Path]::GetFullPath((Join-Path $Root $normalized))
        }
    }
    $projectCandidate = Join-Path $ProjectRoot $normalized
    if (Test-Path -LiteralPath $projectCandidate) {
        return (Resolve-Path -LiteralPath $projectCandidate).Path
    }
    $workflowCandidate = Join-Path $Root $normalized
    if (Test-Path -LiteralPath $workflowCandidate) {
        return (Resolve-Path -LiteralPath $workflowCandidate).Path
    }
    if ($ForOutput) {
        return [System.IO.Path]::GetFullPath($projectCandidate)
    }
    return [System.IO.Path]::GetFullPath($projectCandidate)
}

function Test-Executable([string]$Executable, [string[]]$PrefixArgs, [string[]]$ProbeArgs) {
    try {
        & $Executable @PrefixArgs @ProbeArgs *> $null
        return ($LASTEXITCODE -eq 0)
    }
    catch {
        return $false
    }
}

function Resolve-PythonSpec {
    if ($script:PythonSpec) { return $script:PythonSpec }

    $candidates = @()
    if ($PythonPath) { $candidates += ,@($PythonPath, @()) }
    if ($env:ART_PYTHON) { $candidates += ,@($env:ART_PYTHON, @()) }
    $localPython = if ($script:IsWindowsPlatform) {
        Join-Path $Root '.venv\Scripts\python.exe'
    }
    else {
        Join-Path $Root '.venv/bin/python'
    }
    if (Test-Path -LiteralPath $localPython) { $candidates += ,@($localPython, @()) }
    $candidates += ,@('python3', @())
    $candidates += ,@('py', @('-3'))
    $candidates += ,@('python', @())

    foreach ($candidate in $candidates) {
        $exe = [string]$candidate[0]
        $prefix = [string[]]$candidate[1]
        if (Test-Executable $exe $prefix @('--version')) {
            $script:PythonSpec = [pscustomobject]@{ Exe = $exe; Prefix = $prefix }
            return $script:PythonSpec
        }
    }
    throw 'Python 3 was not found. Set -PythonPath or ART_PYTHON.'
}

function Resolve-BlenderExe {
    if ($script:BlenderExe) { return $script:BlenderExe }
    $candidates = [System.Collections.Generic.List[string]]::new()
    if ($BlenderPath) { $candidates.Add($BlenderPath) }
    if ($env:ART_BLENDER) { $candidates.Add($env:ART_BLENDER) }
    $candidates.Add('blender')

    if ($script:IsWindowsPlatform) {
        $programFiles = @($env:ProgramFiles, ${env:ProgramFiles(x86)}) | Where-Object { $_ }
        foreach ($base in $programFiles) {
            $foundation = Join-Path $base 'Blender Foundation'
            if (-not (Test-Path -LiteralPath $foundation)) { continue }
            Get-ChildItem -LiteralPath $foundation -Filter blender.exe -Recurse -ErrorAction SilentlyContinue |
                Sort-Object FullName -Descending |
                ForEach-Object { $candidates.Add($_.FullName) }
        }
    }
    elseif ($script:IsMacOSPlatform) {
        $candidates.Add('/Applications/Blender.app/Contents/MacOS/Blender')
    }

    foreach ($candidate in $candidates | Select-Object -Unique) {
        if (Test-Executable $candidate @() @('--version')) {
            $script:BlenderExe = $candidate
            return $script:BlenderExe
        }
    }
    throw 'Blender was not found. Set -BlenderPath or ART_BLENDER.'
}

function Resolve-RokitTool([string]$Name) {
    $fileName = if ($script:IsWindowsPlatform) { "$Name.exe" } else { $Name }
    $candidates = [System.Collections.Generic.List[string]]::new()
    if ($RokitBin) { $candidates.Add((Join-Path $RokitBin $fileName)) }
    if ($env:ART_ROKIT_BIN) { $candidates.Add((Join-Path $env:ART_ROKIT_BIN $fileName)) }
    if ($script:IsWindowsPlatform -and $env:USERPROFILE) {
        $candidates.Add((Join-Path $env:USERPROFILE ".rokit\bin\$fileName"))
    }
    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if ($command) { $candidates.Add($command.Source) }
    foreach ($candidate in $candidates | Select-Object -Unique) {
        if (Test-Path -LiteralPath $candidate) { return (Resolve-Path -LiteralPath $candidate).Path }
    }
    throw "$Name was not found. Set -RokitBin or ART_ROKIT_BIN."
}

function Assert-ToolVersion([string]$Executable, [string]$Expected, [string]$Label) {
    $versionOutput = @(& $Executable --version 2>&1)
    $exitCode = $LASTEXITCODE
    $output = ($versionOutput | Select-Object -First 1) -join ''
    if ($exitCode -ne 0 -or $output -notmatch [Regex]::Escape($Expected)) {
        throw "$Label version '$output' does not match pinned $Expected."
    }
    Write-Host "[PASS] $Label $Expected"
}

function Assert-BlenderVersion([string]$Executable) {
    $versionOutput = @(& $Executable --version 2>&1)
    $exitCode = $LASTEXITCODE
    $output = ($versionOutput | Select-Object -First 1) -join ''
    if ($exitCode -ne 0 -or $output -notmatch "Blender\s+$([Regex]::Escape($ExpectedBlenderVersion))") {
        throw "Blender version '$output' does not match pinned $ExpectedBlenderVersion."
    }
    Write-Host "[PASS] Blender $ExpectedBlenderVersion"
}

function Invoke-Checked([string]$Executable, [string[]]$Arguments, [string]$Label) {
    Write-Host "> $Label"
    & $Executable @Arguments
    $code = $LASTEXITCODE
    if ($code -ne 0) {
        throw "$Label failed with exit code $code."
    }
}

function Invoke-CheckedLogged([string]$Executable, [string[]]$Arguments, [string]$Label, [string]$LogPath) {
    Write-Host "> $Label"
    $parent = Split-Path -Parent $LogPath
    if ($parent) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
    & $Executable @Arguments *> $LogPath
    $code = $LASTEXITCODE
    if ($code -ne 0) {
        Write-Host "[FAIL] $Label; final log lines follow:" -ForegroundColor Red
        Get-Content -LiteralPath $LogPath -Tail 80
        throw "$Label failed with exit code $code. Full log: $LogPath"
    }
    Write-Host "[PASS] $Label (log: $LogPath)"
}

function Invoke-Python([string[]]$Arguments, [string]$Label) {
    $spec = Resolve-PythonSpec
    Invoke-Checked $spec.Exe @($spec.Prefix + $Arguments) $Label
}

function Assert-PythonDependencies {
    Invoke-Python @('-m', 'tools.art.check_dependencies') 'Pinned Python dependencies'
}

function Invoke-OptionalR3DDoctor {
    if (-not $UseR3DDoctor) { return }
    $candidate = Join-Path $ProjectRoot 'scripts/r3d.ps1'
    if (-not (Test-Path $candidate)) {
        throw "-UseR3DDoctor was requested but no existing r3d runner was found at $candidate"
    }
    Write-Section 'Existing r3d doctor'
    & $candidate doctor --repo $ProjectRoot
    if ($LASTEXITCODE -ne 0) { throw "r3d doctor failed with exit code $LASTEXITCODE." }
}

function Invoke-CanonPreflight([string]$TerritoryId, [string]$Scope) {
    $args = @(
        '-m', 'tools.art.prepare_canon_generation',
        '--territory', $TerritoryId,
        '--scope', $Scope
    )
    if ($RequireLockedCanons) { $args += '--production' }
    Invoke-Python $args "Bind $Scope generation to visual canons: $TerritoryId"
}

function Invoke-CanonCompliance(
    [string]$TerritoryId,
    [string]$AssetId,
    [string]$Scope,
    [string]$BuildReport,
    [string]$ComponentEvidence
) {
    $canon = Join-Path $Root "art/canonical-visuals/$TerritoryId/$AssetId.json"
    $authority = Join-Path $Root "build/canon-authority/$TerritoryId`__$Scope.json"
    $output = Join-Path $Root "build/canon-compliance/$TerritoryId/$AssetId.json"
    $args = @(
        '-m', 'tools.art.build_canon_compliance',
        $canon, $BuildReport, $authority,
        '--output', $output
    )
    if ($ComponentEvidence) {
        $args += @('--component-evidence', $ComponentEvidence)
    }
    Invoke-Python $args "Canon compliance: $TerritoryId/$AssetId"
}

function Import-UserStagingEnvironment([bool]$IncludeOpenCloudKey) {
    if (-not $script:IsWindowsPlatform) { return }
    $names = @(
        'ROBLOX_STAGING_CREATOR_ID',
        'ROBLOX_3D_ALLOWED_CREATOR_IDS'
    )
    if ($IncludeOpenCloudKey) {
        $names = @('ROBLOX_OPEN_CLOUD_API_KEY') + $names
    }
    else {
        [Environment]::SetEnvironmentVariable(
            'ROBLOX_OPEN_CLOUD_API_KEY',
            $null,
            'Process'
        )
    }
    foreach ($name in $names) {
        if (Test-Path "Env:$name") { continue }
        $value = [Environment]::GetEnvironmentVariable($name, 'User')
        if ($value) {
            [Environment]::SetEnvironmentVariable($name, $value, 'Process')
        }
    }
}

function Test-CurrentBuildReport([string]$TerritoryId, [string]$Mode, [bool]$RequireReview) {
    $reportPath = Join-Path $Root "build/$TerritoryId/build-report.json"
    if (-not (Test-Path -LiteralPath $reportPath -PathType Leaf)) { return $false }
    $spec = Resolve-PythonSpec
    & $spec.Exe @($spec.Prefix + @('-m', 'tools.art.validate_build_report', $reportPath)) *> $null
    if ($LASTEXITCODE -ne 0) { return $false }
    try {
        $reportData = Get-Content -LiteralPath $reportPath -Raw | ConvertFrom-Json
        if ($reportData.renderMode -ne $Mode) { return $false }
        if ($RequireReview -and (-not $reportData.reviewRequested -or $reportData.reviewEvidence.Count -eq 0)) { return $false }
        return $true
    }
    catch {
        return $false
    }
}

function Invoke-ArtBuild([string]$Mode, [bool]$IncludeReview) {
    Invoke-OptionalR3DDoctor
    Invoke-Python @('-m', 'tools.art.validate_library', '--report', 'evidence/static-validation-report.json') 'Pre-build validation'
    $blender = Resolve-BlenderExe
    Assert-BlenderVersion $blender
    $territories = if ($Territory) { @($Territory) } else { @('industrial-toy-defense', 'salvaged-frontier', 'clean-tactical-diorama') }
    if ($DryRun) {
        Write-Host "[DRY-RUN] Build mode=$Mode review=$IncludeReview territories=$($territories -join ',')"
        return
    }
    foreach ($territoryId in $territories) {
        Invoke-CanonPreflight $territoryId 'calibration'
        if ($Resume -and (Test-CurrentBuildReport $territoryId $Mode $IncludeReview)) {
            Write-Host "[RESUME] Reusing current hash-validated build: $territoryId"
        }
        else {
            $args = @(
                '--background',
                '--factory-startup',
                '--threads', '1',
                '--python-exit-code', '19',
                '--python', (Join-Path $Root 'tools/blender/build_art_direction.py'),
                '--',
                '--root', $Root,
                '--territory', $territoryId,
                '--render-mode', $Mode
            )
            if ($IncludeReview) { $args += '--review-renders' }
            $logPath = Join-Path $Root "build/logs/$territoryId`__$Mode.log"
            Invoke-CheckedLogged $blender $args "Blender build: $territoryId" $logPath
        }
        $reportPath = Join-Path $Root "build/$territoryId/build-report.json"
        $validateArgs = @('-m', 'tools.art.validate_build_report', $reportPath)
        if ($Mode -eq 'full') { $validateArgs += '--require-complete' }
        Invoke-Python $validateArgs "Validate Blender report: $territoryId"
        $componentEvidencePath = Join-Path $Root "build/$territoryId/component-evidence-report.json"
        Invoke-CheckedLogged $blender @(
            '--background',
            '--factory-startup',
            '--threads', '1',
            '--python-exit-code', '19',
            '--python', (Join-Path $Root 'tools/blender/inspect_component_evidence.py'),
            '--',
            '--build-report', $reportPath,
            '--output', $componentEvidencePath
        ) "Inspect semantic components: $territoryId" (Join-Path $Root "build/logs/$territoryId`__components.log")
        foreach ($assetId in @('barricade', 'objective_core', 'enemy_standard', 'floor_module', 'damage_effect')) {
            Invoke-CanonCompliance $territoryId $assetId 'calibration' $reportPath $componentEvidencePath
        }
    }
    if (-not $Territory -and $Mode -eq 'smoke') {
        Invoke-Python @('-m', 'tools.art.capture_smoke_evidence') 'Capture package-safe smoke evidence'
    }
    if (-not $Territory -and $Mode -eq 'full') {
        Invoke-Python @('-m', 'tools.art.capture_full_evidence') 'Capture package-safe full evidence'
    }
    Write-Host '[PASS] Blender builds completed. Studio, physical-device, and human evidence remain separate gates.'
}

function Invoke-ReviewGallery {
    $args = @('-m', 'tools.art.build_review_gallery')
    if ($Output) { $args += @('--output', $Output) }
    if ($Territory) { $args += @('--territory', $Territory) }
    Invoke-Python $args 'Build hash-validated review gallery'
    $gallery = if ($Output) { Join-Path $Output 'index.html' } else { Join-Path $Root 'build/review/index.html' }
    if ($Open) {
        if (-not (Test-Path -LiteralPath $gallery -PathType Leaf)) { throw "Review gallery was not created: $gallery" }
        Start-Process -FilePath (Resolve-Path -LiteralPath $gallery).Path
    }
}

Push-Location $Root
try {
    switch ($Command) {
        'bootstrap' {
            Write-Section 'Package-local Python bootstrap'
            $base = Resolve-PythonSpec
            $venvPython = if ($script:IsWindowsPlatform) {
                Join-Path $Root '.venv\Scripts\python.exe'
            }
            else {
                Join-Path $Root '.venv/bin/python'
            }
            if (-not (Test-Path -LiteralPath $venvPython)) {
                Invoke-Checked $base.Exe @($base.Prefix + @('-m', 'venv', (Join-Path $Root '.venv'))) 'Create local virtual environment'
            }
            Invoke-Checked $venvPython @('-m', 'pip', 'install', '--disable-pip-version-check', '--requirement', (Join-Path $Root 'requirements-dev.txt')) 'Install pinned dependencies'
            $script:PythonSpec = [pscustomobject]@{ Exe = $venvPython; Prefix = @() }
            Assert-PythonDependencies
            Write-Host '[PASS] Package-local Python environment is ready.'
        }
        'doctor' {
            Write-Section 'Art-direction doctor'
            $py = Resolve-PythonSpec
            & $py.Exe @($py.Prefix + @('--version'))
            Write-Host "Root: $Root"
            Write-Host "Python: $($py.Exe) $($py.Prefix -join ' ')"
            Assert-PythonDependencies
            try {
                $blender = Resolve-BlenderExe
                Assert-BlenderVersion $blender
                & $blender --version | Select-Object -First 2
                Write-Host "Blender: $blender"
            }
            catch {
                Write-Warning $_.Exception.Message
                Write-Host 'Blender execution status: BLOCKED_IN_THIS_ENVIRONMENT'
            }
            Invoke-OptionalR3DDoctor
            Invoke-Python @('-m', 'tools.art.validate_library', '--report', 'evidence/static-validation-report.json') 'Static validation'
        }
        'precanon-init' {
            Write-Section 'Deterministic precanonical request'
            if (-not $Brief -or -not $RequestId -or -not $Output) {
                throw 'precanon-init requires -Brief, -RequestId, and -Output.'
            }
            $resolvedBrief = Resolve-WorkflowPath $Brief
            $resolvedOutput = Resolve-WorkflowPath $Output $true
            $args = @(
                '-m', 'tools.art.precanonical', 'init',
                '--brief', $resolvedBrief,
                '--request-id', $RequestId,
                '--output', $resolvedOutput,
                '--stage', $PrecanonicalStage,
                '--browser-adapter', $BrowserAdapter,
                '--maximum-generations', [string]$MaximumWebGenerations
            )
            if ($NoHumanConfirmation) { $args += '--no-human-confirmation' }
            if ($AuthorizeAutomaticSubmission) { $args += '--authorize-automatic-submission' }
            if ($Result) { $args += @('--parent-result', (Resolve-WorkflowPath $Result)) }
            foreach ($instruction in @($RevisionInstruction)) {
                if ($instruction) { $args += @('--revision-instruction', $instruction) }
            }
            Invoke-Python $args 'Compile precanonical packet'
        }
        'precanon-preflight' {
            Write-Section 'Zero-consumption Web preflight'
            if (-not $Request) { throw 'precanon-preflight requires -Request.' }
            $args = @('-m', 'tools.art.precanonical', 'preflight', (Resolve-WorkflowPath $Request))
            if ($Output) { $args += @('--output', (Resolve-WorkflowPath $Output $true)) }
            Invoke-Python $args 'Validate prompt, hashes, budget and authority'
        }
        'precanon-browser-doctor' {
            Write-Section 'Codex Browser installation and capability doctor'
            if (-not $Output) {
                throw 'precanon-browser-doctor requires -Output.'
            }
            Invoke-Python @(
                '-m', 'tools.art.precanonical', 'browser-doctor',
                '--browser-adapter', $BrowserAdapter,
                '--output', (Resolve-WorkflowPath $Output $true)
            ) 'Verify the app-managed browser runtime without claiming task exposure'
        }
        'precanon-handoff' {
            Write-Section 'Sanitized ChatGPT Web handoff'
            if (-not $Request -or -not $Preflight -or -not $BrowserDoctor -or -not $Output) {
                throw 'precanon-handoff requires -Request, -Preflight, -BrowserDoctor, and -Output.'
            }
            Invoke-Python @(
                '-m', 'tools.art.precanonical', 'handoff', (Resolve-WorkflowPath $Request),
                '--preflight', (Resolve-WorkflowPath $Preflight),
                '--browser-doctor', (Resolve-WorkflowPath $BrowserDoctor),
                '--output', (Resolve-WorkflowPath $Output $true)
            ) 'Prepare task-scoped Web transport handoff without submission'
        }
        'precanon-operator' {
            Write-Section 'Semi-automatic precanonical operator'
            if (-not $Request -or -not $Output) {
                throw 'precanon-operator requires -Request and -Output.'
            }
            $operatorCommand = if ($DryRun) { 'prepare' } else { 'serve' }
            $args = @(
                '-m', 'tools.art.precanonical_operator', $operatorCommand,
                '--request', (Resolve-WorkflowPath $Request),
                '--output', (Resolve-WorkflowPath $Output $true)
            )
            if (-not $DryRun) {
                $args += @(
                    '--port', [string]$Port,
                    '--idle-timeout-minutes', [string]$IdleTimeoutMinutes
                )
                if (-not $NoOpen) { $args += '--open' }
            }
            Invoke-Python $args 'Prepare the loopback-only human bridge and bounded intake'
        }
        'precanon-campaign-init' {
            Write-Section 'Object-by-state precanonical campaign'
            if (-not $Output) {
                throw 'precanon-campaign-init requires -Output.'
            }
            Invoke-Python @(
                '-m', 'tools.art.precanonical_campaign', 'init',
                '--output', (Resolve-WorkflowPath $Output $true),
                '--campaign-id', $CampaignId,
                '--max-attempts-per-task', [string]$MaxAttemptsPerTask
            ) 'Compile six objects and sixteen state-specific GPT Image 2 tasks'
        }
        'precanon-campaign-snapshot' {
            Write-Section 'Immutable campaign canon snapshot'
            if (-not $Campaign) {
                throw 'precanon-campaign-snapshot requires -Campaign.'
            }
            Invoke-Python @(
                '-m', 'tools.art.precanonical_campaign', 'snapshot',
                (Resolve-WorkflowPath $Campaign)
            ) 'Snapshot exact campaign-bound canons before a visual-authority revision'
        }
        'precanon-campaign-fork' {
            Write-Section 'Versioned precanonical campaign revision'
            if (-not $SourceCampaign -or -not $Output -or -not $RestartTaskId -or -not $RevisionReason) {
                throw 'precanon-campaign-fork requires -SourceCampaign, -Output, -RestartTaskId, and -RevisionReason.'
            }
            Invoke-Python @(
                '-m', 'tools.art.precanonical_campaign', 'fork',
                '--source-campaign', (Resolve-WorkflowPath $SourceCampaign),
                '--output', (Resolve-WorkflowPath $Output $true),
                '--campaign-id', $CampaignId,
                '--restart-task-id', $RestartTaskId,
                '--reason', $RevisionReason
            ) 'Carry accepted prefix evidence and restart from the revised canon'
        }
        'precanon-campaign-operator' {
            Write-Section 'Continuous object-by-state precanonical operator'
            if (-not $Campaign -or -not $Output) {
                throw 'precanon-campaign-operator requires -Campaign and -Output.'
            }
            $operatorCommand = if ($DryRun) { 'prepare-campaign' } else { 'serve-campaign' }
            $args = @(
                '-m', 'tools.art.precanonical_operator', $operatorCommand,
                '--campaign', (Resolve-WorkflowPath $Campaign),
                '--output', (Resolve-WorkflowPath $Output $true)
            )
            if (-not $DryRun) {
                $args += @(
                    '--port', [string]$Port,
                    '--idle-timeout-minutes', [string]$IdleTimeoutMinutes
                )
                if (-not $NoOpen) { $args += '--open' }
            }
            Invoke-Python $args 'Run the continuous sixteen-task human operator'
        }
        'precanon-import' {
            Write-Section 'Precanonical Web result intake'
            if (-not $Request -or -not $ResultId -or -not $Output -or -not $Image) {
                throw 'precanon-import requires -Request, -ResultId, -Output, and at least one -Image.'
            }
            $args = @(
                '-m', 'tools.art.precanonical', 'import', (Resolve-WorkflowPath $Request),
                '--result-id', $ResultId,
                '--output', (Resolve-WorkflowPath $Output $true),
                '--download-method', $DownloadMethod
            )
            foreach ($imagePath in $Image) {
                $args += @('--image', (Resolve-WorkflowPath $imagePath))
            }
            if ($ModelName) { $args += @('--model-name', $ModelName) }
            if ($ModelNameUiConfirmed) { $args += '--model-name-ui-confirmed' }
            Invoke-Python $args 'Import downloaded image with conservative provenance'
        }
        'precanon-review' {
            Write-Section 'Precanonical visual review'
            if (-not $Result -or -not $RequestId -or -not $ReviewDecision -or -not $Output) {
                throw 'precanon-review requires -Result, -RequestId as review ID, -ReviewDecision, and -Output.'
            }
            $args = @(
                '-m', 'tools.art.precanonical', 'review', (Resolve-WorkflowPath $Result),
                '--review-id', $RequestId,
                '--decision', $ReviewDecision,
                '--output', (Resolve-WorkflowPath $Output $true)
            )
            if ($Assessment) { $args += @('--assessment', (Resolve-WorkflowPath $Assessment)) }
            if ($Reviewer) { $args += @('--reviewer', $Reviewer) }
            foreach ($value in @($Preserve)) {
                if ($value) { $args += @('--preserve', $value) }
            }
            foreach ($value in @($Correct)) {
                if ($value) { $args += @('--correct', $value) }
            }
            foreach ($value in @($ForbidNext)) {
                if ($value) { $args += @('--forbid-next', $value) }
            }
            Invoke-Python $args 'Record bounded result decision'
        }
        'precanon-status' {
            Write-Section 'Precanonical request status'
            if (-not $Request) { throw 'precanon-status requires -Request.' }
            Invoke-Python @('-m', 'tools.art.precanonical', 'status', (Resolve-WorkflowPath $Request)) 'Inspect request, results and reviews'
        }
        'canons' {
            Write-Section 'Canonical visual definitions'
            Assert-PythonDependencies
            Invoke-Python @('-m', 'tools.art.build_visual_canons') 'Compile 18 object x art-direction canons'
            Invoke-Python @('-m', 'tools.art.build_visual_canons', '--check') 'Verify canon determinism and coverage'
        }
        'validate-canons' {
            Write-Section 'Canonical visual definition gates'
            Assert-PythonDependencies
            $args = @('-m', 'tools.art.build_visual_canons', '--check')
            if ($RequireLockedCanons) { $args += '--require-locked' }
            $py = Resolve-PythonSpec
            Write-Host '> Validate visual canons'
            & $py.Exe @($py.Prefix + $args)
            $code = $LASTEXITCODE
            if ($code -eq 2) {
                Write-Host '[BLOCKED] Selected visual canons still require multimodal evidence and human approval.' -ForegroundColor Yellow
                exit 2
            }
            if ($code -ne 0) {
                throw "Validate visual canons failed with exit code $code."
            }
        }
        'lock-canon' {
            Write-Section 'Human visual canon lock'
            if (-not $Asset -or -not $Territory -or -not $CanonEvidence) {
                throw 'lock-canon requires -Asset, -Territory, and -CanonEvidence.'
            }
            $args = @(
                '-m', 'tools.art.lock_visual_canon',
                '--asset', $Asset,
                '--territory', $Territory,
                '--evidence-manifest', (Resolve-WorkflowPath $CanonEvidence)
            )
            if ($HumanReview) {
                $args += @('--human-review', (Resolve-WorkflowPath $HumanReview))
            }
            else {
                if (-not $LockedBy -or -not $DecisionRecord) {
                    throw 'lock-canon requires -HumanReview, or legacy -LockedBy and -DecisionRecord for synthetic dry-run previews.'
                }
                $args += @('--approved-by', $LockedBy, '--decision-record', $DecisionRecord)
            }
            if ($Apply) { $args += '--apply' }
            Invoke-Python $args 'Validate or apply visual canon lock'
            if ($Apply) {
                Invoke-Python @('-m', 'tools.art.build_visual_canons') 'Rebuild canons from approved lock overlay'
                Invoke-Python @('-m', 'tools.art.build_visual_canons', '--check') 'Verify locked canon determinism'
            }
        }
        'validate' {
            Write-Section 'Strict validation'
            Assert-PythonDependencies
            Invoke-Python @('-m', 'tools.art.build_visual_canons', '--check') 'Visual canon drift and coverage'
            Invoke-Python @('-m', 'tools.art.generate_luau', '--check') 'Generated-code drift check'
            Invoke-Python @('-m', 'tools.art.validate_library', '--report', 'evidence/static-validation-report.json') 'Schema and semantic validation'
        }
        'generate' {
            Write-Section 'Generate Studio configuration'
            Assert-PythonDependencies
            Invoke-Python @('-m', 'tools.art.build_visual_canons') 'Compile canonical visual definitions'
            Invoke-Python @('-m', 'tools.art.generate_luau') 'Generate Luau from canonical JSON'
            Invoke-Python @('-m', 'tools.art.validate_library', '--report', 'evidence/static-validation-report.json') 'Post-generation validation'
        }
        'test' {
            Write-Section 'Adversarial regression tests'
            Assert-PythonDependencies
            Invoke-Python @('-m', 'tools.art.build_transfer_import_queue') 'Prepare portable transfer test queue'
            Invoke-Python @('-m', 'pytest') 'pytest'
            Invoke-Python @('tools/roblox-3d-asset/r3d.py', 'test') 'Per-asset r3d tests'
        }
        'validate-luau' {
            Write-Section 'Luau static validation'
            $stylua = Resolve-RokitTool 'stylua'
            $selene = Resolve-RokitTool 'selene'
            $luauLsp = Resolve-RokitTool 'luau-lsp'
            Assert-ToolVersion $stylua $ExpectedRokitToolVersions['stylua'] 'StyLua'
            Assert-ToolVersion $selene $ExpectedRokitToolVersions['selene'] 'Selene'
            Assert-ToolVersion $luauLsp $ExpectedRokitToolVersions['luau-lsp'] 'Luau LSP'
            $handAuthored = @(Get-ChildItem -LiteralPath (Join-Path $Root 'studio/src'), (Join-Path $Root 'studio/plugin') -Recurse -File | Where-Object { $_.Extension -eq '.luau' } | ForEach-Object { $_.FullName })
            $typed = @(
                'studio/src/AssetKitStager.luau',
                'studio/src/GoldenSceneBuilder.luau',
                'studio/src/GoldenSceneValidator.luau',
                'studio/src/LightingProfileService.luau',
                'studio/src/PerformanceBenchmarkBuilder.luau',
                'studio/generated/ArtDirectionConfig.luau',
                'studio/generated/LightingProfiles.luau',
                'studio/generated/TerritoryStyles.luau'
            ) | ForEach-Object { (Resolve-Path -LiteralPath (Join-Path $Root $_)).Path }
            $styluaArgs = @('--config-path', (Join-Path $Root 'studio/tooling/stylua.toml'), '--verify', '--check') + $handAuthored
            Invoke-Checked $stylua $styluaArgs 'StyLua hand-authored Studio sources'
            $seleneArgs = @('--config', (Join-Path $Root 'studio/tooling/selene.toml')) + $handAuthored
            Invoke-Checked $selene $seleneArgs 'Selene hand-authored Studio sources'
            $definitions = "@roblox=$(Join-Path $Root 'studio/tooling/globalTypes.d.luau')"
            $lspArgs = @('analyze', '--platform', 'roblox', '--definitions', $definitions) + $typed
            Invoke-Checked $luauLsp $lspArgs 'Luau LSP core and generated modules'
            Write-Host '[PASS] Hand-authored Luau is formatted/linted; core and generated modules type-check.'
            Write-Host '[SKIP] Plugin/CaptureController type resolution requires the installed Studio hierarchy sourcemap.'
        }
        'build' {
            Write-Section 'Blender deterministic build'
            Assert-PythonDependencies
            Invoke-ArtBuild $RenderMode ([bool]$ReviewRenders)
        }
        'review' {
            Write-Section 'Local review gallery'
            Assert-PythonDependencies
            Invoke-ReviewGallery
        }
        'workbench' {
            Write-Section 'One-command art-direction workbench'
            Assert-PythonDependencies
            Invoke-Python @('-m', 'tools.art.build_visual_canons') 'Compile canonical visual definitions'
            Invoke-Python @('-m', 'tools.art.generate_luau') 'Generate Studio configuration'
            Invoke-Python @('-m', 'tools.art.archive_stale_evidence') 'Archive stale Blender evidence'
            Invoke-Python @('-m', 'tools.art.validate_library', '--report', 'evidence/static-validation-report.json') 'Validate contracts and generated code'
            Invoke-ArtBuild $RenderMode $true
            if (-not $DryRun) {
                if ($RenderMode -eq 'full') {
                    Invoke-Python @('-m', 'tools.art.build_studio_import_queue') 'Build flat Studio import queue'
                }
                else {
                    Write-Host '[SKIP] Studio import queue requires RenderMode=full.'
                }
            }
            $blender = Resolve-BlenderExe
            Invoke-Python @('-m', 'tools.art.verify_blender', '--blender', $blender) 'Verify A/B Blender determinism'
            if (-not $DryRun) { Invoke-ReviewGallery }
            Invoke-Python @('-m', 'pytest', '-q') 'Run adversarial regression tests against current evidence'
            Invoke-Python @('tools/roblox-3d-asset/r3d.py', 'test') 'Run per-asset r3d tests'
            Write-Host '[PASS] Workbench completed. Open build/review/index.html for human review.'
        }
        'simulate-workflow' {
            Write-Section 'Complete non-production workflow simulation'
            Assert-PythonDependencies
            Invoke-Python @('-m', 'tools.art.build_visual_canons') 'Compile canonical visual definitions'
            Invoke-Python @('-m', 'tools.art.generate_luau') 'Generate Studio configuration'
            Invoke-Python @('-m', 'tools.art.archive_stale_evidence') 'Archive stale Blender evidence'
            Invoke-Python @('-m', 'tools.art.validate_library', '--report', 'evidence/static-validation-report.json') 'Validate contracts and generated code'

            Invoke-ArtBuild 'full' $true
            Invoke-Python @('-m', 'tools.art.build_studio_import_queue') 'Build full-evidence Studio import queue'
            $blender = Resolve-BlenderExe
            Invoke-Python @('-m', 'tools.art.verify_blender', '--blender', $blender) 'Verify A/B Blender determinism'
            Invoke-Python @('-m', 'tools.art.measure_visual_quality') 'Measure current full-build visual quality'

            foreach ($territoryId in @('industrial-toy-defense', 'salvaged-frontier', 'clean-tactical-diorama')) {
                Invoke-CanonPreflight $territoryId 'transfer'
            }
            Invoke-Python @('-m', 'tools.art.build_transfer_proof', '--blender', $blender) 'Rebuild deterministic sixth-asset transfer proof'
            Invoke-Python @('-m', 'tools.art.validate_transfer_report', 'evidence/transfer/turret-fast-v1/report.json') 'Validate automated sixth-asset transfer proof'
            Invoke-Python @('-m', 'tools.art.build_transfer_import_queue') 'Build nine-candidate transfer queue'

            $simulationOutput = if ($Output) {
                Resolve-WorkflowPath $Output $true
            }
            else {
                Join-Path $Root 'build/simulations/complete-workflow/current'
            }
            Invoke-Python @(
                '-m', 'tools.art.simulate_complete_workflow',
                '--output', $simulationOutput
            ) 'Run isolated human, mobile, cloud and Studio doubles'
            Invoke-Python @('-m', 'pytest', '-q') 'Run adversarial regression tests'
            Invoke-Python @('tools/roblox-3d-asset/r3d.py', 'test') 'Run per-asset r3d tests'
            Write-Host '[PASS] Complete simulation passed. Real production approval remains false.'
        }
        'verify-blender' {
            Write-Section 'Blender integration and determinism verification'
            Assert-PythonDependencies
            $blender = Resolve-BlenderExe
            Assert-BlenderVersion $blender
            Invoke-Python @('-m', 'tools.art.verify_blender', '--blender', $blender) 'Verify Blender builds and determinism'
        }
        'measure-visual' {
            Write-Section 'State and territory silhouette metrics'
            Assert-PythonDependencies
            Invoke-Python @('-m', 'tools.art.measure_visual_quality') 'Measure current full-build visual quality'
        }
        'transfer' {
            Write-Section 'Independent sixth-asset transfer proof'
            Assert-PythonDependencies
            $blender = Resolve-BlenderExe
            Assert-BlenderVersion $blender
            foreach ($territoryId in @('industrial-toy-defense', 'salvaged-frontier', 'clean-tactical-diorama')) {
                Invoke-CanonPreflight $territoryId 'transfer'
            }
            if ($DryRun) {
                Write-Host '[DRY-RUN] Would build turret_fast_v1 twice for determinism and once with 36 renders in each of the three territories.'
                return
            }
            $args = @('-m', 'tools.art.build_transfer_proof', '--blender', $blender)
            if ($RequirePass) { $args += '--require-approved' }
            Invoke-Python $args 'Build deterministic sixth-asset transfer proof'
            Invoke-Python @(
                '-m', 'tools.art.validate_transfer_report',
                'evidence/transfer/turret-fast-v1/report.json'
            ) 'Validate portable transfer evidence'
            Invoke-Python @(
                '-m', 'tools.art.build_transfer_import_queue'
            ) 'Build nine-GLB Studio transfer import queue'
            Invoke-Python @(
                '-m', 'tools.art.validate_library',
                '--report', 'evidence/static-validation-report.json'
            ) 'Validate workflow after transfer proof'
            foreach ($territoryId in @('industrial-toy-defense', 'salvaged-frontier', 'clean-tactical-diorama')) {
                $transferBuildReport = Join-Path $Root "build/transfer/turret_fast_v1/$territoryId/transfer-build-report.json"
                Invoke-CanonCompliance $territoryId 'turret_fast_v1' 'transfer' $transferBuildReport
            }
            $gallery = Join-Path $Root 'evidence/transfer/turret-fast-v1/review/index.html'
            Write-Host "[PASS] Automated transfer proof is current. Human authority remains explicit in art/transfer/turret-fast-v1-review.json."
            Write-Host "Review gallery: $gallery"
            Write-Host "Studio import queue: $(Join-Path $Root 'build/studio-import-transfer')"
            if ($Open) {
                Start-Process -FilePath (Resolve-Path -LiteralPath $gallery).Path
            }
        }
        'validate-transfer' {
            $transferReport = if ($Report) {
                $Report
            }
            else {
                Join-Path $Root 'evidence/transfer/turret-fast-v1/report.json'
            }
            $args = @('-m', 'tools.art.validate_transfer_report', $transferReport)
            if ($RequirePass) { $args += '--require-approved' }
            Invoke-Python $args 'Validate sixth-asset transfer report'
        }
        'publish-transfer' {
            Write-Section 'Staging-only transfer candidate publication'
            Assert-PythonDependencies
            Import-UserStagingEnvironment $true
            Invoke-Python @('-m', 'tools.art.build_transfer_import_queue') 'Prepare transfer upload queue'
            $args = @('-m', 'tools.art.publish_transfer_candidates')
            if ($ConfirmPublish) {
                $args += '--confirm-publish'
            }
            else {
                $args += '--dry-run'
            }
            Invoke-Python $args 'Publish immutable transfer candidates'
        }
        'stage-transfer' {
            Write-Section 'Transactional Studio transfer integration'
            Assert-PythonDependencies
            Import-UserStagingEnvironment $false
            $args = @('-m', 'tools.art.stage_transfer_studio')
            if ($Apply) {
                $args += '--apply'
            }
            else {
                $args += '--dry-run'
            }
            if ($ReviewRenders) { $args += '--capture' }
            Invoke-Python $args 'Stage and validate transfer candidates in Studio'
        }
        'validate-studio' {
            if (-not $Report) { throw 'validate-studio requires -Report.' }
            $reportPath = Resolve-WorkflowPath $Report
            $args = @('-m', 'tools.art.validate_studio_report', $reportPath)
            if ($RequirePass) { $args += '--require-pass' }
            Invoke-Python $args 'Validate Studio Golden Scene report'
        }
        'bind-studio-captures' {
            if (-not $Report) { throw 'bind-studio-captures requires -Report.' }
            $reportPath = Resolve-WorkflowPath $Report
            Invoke-Python @('-m', 'tools.art.bind_studio_captures', $reportPath) 'Bind Studio captures to report'
        }
        'validate-mobile' {
            if (-not $Report) { throw 'validate-mobile requires -Report.' }
            $reportPath = Resolve-WorkflowPath $Report
            $args = @('-m', 'tools.art.validate_performance_report', $reportPath)
            if ($RequirePass) { $args += '--require-pass' }
            Invoke-Python $args 'Validate physical-device mobile report'
        }
        'validate-simulator' {
            if (-not $Report) { throw 'validate-simulator requires -Report.' }
            $reportPath = Resolve-WorkflowPath $Report
            $args = @('-m', 'tools.art.validate_studio_simulator_report', $reportPath)
            if ($RequirePass) { $args += '--require-pass' }
            Invoke-Python $args 'Validate Studio simulator report'
        }
        'package' {
            Assert-PythonDependencies
            Invoke-Python @('-m', 'tools.art.verify_static', '--output', 'evidence/static-verification-report.json') 'Run complete static verification'
            Invoke-Python @('-m', 'tools.art.validate_library', '--report', 'evidence/static-validation-report.json') 'Validate fresh verification evidence'
            $archive = if ($Output) { $Output } else { Join-Path (Split-Path $Root -Parent) 'roblox-art-bible-sota-v3.zip' }
            Invoke-Python @('-m', 'tools.art.package_release', '--output', $archive) 'Build deterministic release archive'
        }
        'evidence-index' {
            Write-Section 'Evidence index'
            if (-not $Territory) { throw 'evidence-index requires -Territory.' }
            Invoke-Python @('-m', 'tools.art.build_evidence_index', '--territory', $Territory) 'Build evidence index template'
        }
        'prepare-study' {
            $studyOutput = if ($Output) { $Output } else { Join-Path $Root 'evidence/human/art-direction-study-v1' }
            $studyEvidenceRoot = if ($EvidenceRoot) { $EvidenceRoot } else { $Root }
            Invoke-Python @(
                '-m', 'tools.art.blind_study', 'prepare',
                '--output', $studyOutput,
                '--evidence-root', $studyEvidenceRoot
            ) 'Prepare sealed-capable blind study'
            if ($Open) {
                Start-Process (Join-Path $studyOutput 'operator/README.md')
            }
        }
        'seal-study' {
            $resolvedStudyRoot = if ($StudyRoot) { $StudyRoot } else { Join-Path $Root 'evidence/human/art-direction-study-v1' }
            $studyEvidenceRoot = if ($EvidenceRoot) { $EvidenceRoot } else { $Root }
            Invoke-Python @(
                '-m', 'tools.art.blind_study', 'seal',
                '--study-root', $resolvedStudyRoot,
                '--evidence-root', $studyEvidenceRoot
            ) 'Validate and seal blind-study submissions'
        }
        'score' {
            if (-not $Submissions -or -not $BlindMap) { throw 'score requires -Submissions and -BlindMap.' }
            $args = @('-m', 'tools.art.score_territories', $Submissions, $BlindMap)
            if ($Output) { $args += @('--output', $Output) }
            if ($RequireEligible) { $args += '--require-eligible' }
            Invoke-Python $args 'Score sealed blind study'
        }
        'lock' {
            if (-not $Decision -or -not $EvidenceIndex -or -not $LockedBy) {
                throw 'lock requires -Decision, -EvidenceIndex, and -LockedBy. -BlindMap and -ScoringReport are required only for a blind-study selection decision.'
            }
            $args = @(
                '-m', 'tools.art.lock_direction',
                $Decision,
                '--evidence-index', $EvidenceIndex,
                '--locked-by', $LockedBy
            )
            if ($BlindMap) { $args += @('--blind-map', $BlindMap) }
            if ($ScoringReport) { $args += @('--scoring-report', $ScoringReport) }
            if ($Apply) { $args += '--apply' }
            Invoke-Python $args 'Validate or apply art lock'
        }
    }
}
finally {
    Pop-Location
}
