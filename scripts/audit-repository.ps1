[CmdletBinding()]
param(
    [string]$RepositoryRoot,
    [string]$OutputDirectory = (Join-Path $env:TEMP "roblox-repository-audit-current"),
    [switch]$IncludeGitMetadata
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($RepositoryRoot)) {
    $RepositoryRoot = Split-Path -Parent $PSScriptRoot
}

function Get-GitExecutable {
    $command = Get-Command git -ErrorAction SilentlyContinue
    if ($command) {
        return $command.Source
    }

    $candidates = @(
        (Join-Path $env:LOCALAPPDATA "Programs\Git\cmd\git.exe"),
        "C:\Program Files\Git\cmd\git.exe",
        "C:\Program Files\Git\bin\git.exe"
    )

    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate -PathType Leaf) {
            return $candidate
        }
    }

    throw "Git is required to classify tracked, untracked, and ignored files."
}

function Get-StringSet {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Values
    )

    $set = [Collections.Generic.HashSet[string]]::new(
        [StringComparer]::OrdinalIgnoreCase
    )
    foreach ($value in $Values) {
        if (-not [string]::IsNullOrWhiteSpace($value)) {
            [void]$set.Add(($value -replace "\\", "/"))
        }
    }
    return ,$set
}

function Add-Count {
    param(
        [Parameter(Mandatory = $true)]
        [Collections.Generic.Dictionary[string, int]]$Dictionary,
        [Parameter(Mandatory = $true)]
        [string]$Key
    )

    if ($Dictionary.ContainsKey($Key)) {
        $Dictionary[$Key]++
    }
    else {
        $Dictionary[$Key] = 1
    }
}

function Get-RepositoryLayer {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RelativePath
    )

    $path = $RelativePath.ToLowerInvariant()
    $leaf = [IO.Path]::GetFileName($path)

    if ($path.StartsWith(".git/")) {
        return "vcs_metadata"
    }
    if (
        $path -match "(^|/)(\.venv|venv|node_modules|site-packages)(/|$)" -or
        $path -match "(^|/)(__pycache__)(/|$)"
    ) {
        return "dependency_environment"
    }
    if (
        $path -match "\.backup-[^/]+(/|$)" -or
        $path -match "(^|/)\.roblox-art-bible-sota-v3\.install-[^/]+(/|$)" -or
        $leaf -match "\.backup-[^/]+$"
    ) {
        return "historical_backup"
    }
    if ($path.StartsWith("tmp/")) {
        return "temporary"
    }
    if ([IO.Path]::GetExtension($path) -in @(".zip", ".7z", ".rar", ".tar", ".gz")) {
        return "archive"
    }
    if (
        $path -match "(^|/)(build|dist|coverage|workbench)(/|$)" -or
        $path -match "(^|/)evidence/local(/|$)"
    ) {
        return "generated_artifact"
    }
    if ($path.StartsWith("data/")) {
        return "gameplay_source"
    }
    if ($path.StartsWith("tests/")) {
        return "test_source"
    }
    if ($path.StartsWith("studio/")) {
        return "studio_contract"
    }
    if ($path.StartsWith("docs/") -or $path.StartsWith("plans/")) {
        return "documentation"
    }
    if ($path.StartsWith("assets-3d/") -or $path.StartsWith("art/")) {
        return "asset_contract"
    }
    if ($path.StartsWith("tools/roblox-art-bible-sota-v3/")) {
        return "art_direction_tool"
    }
    if ($path.StartsWith("tools/roblox-3d-asset/")) {
        return "asset_pipeline_tool"
    }
    if ($path.StartsWith("tools/")) {
        return "tooling_dependency"
    }
    if ($path.StartsWith("scripts/")) {
        return "repository_tooling"
    }
    if ($path.StartsWith(".agents/")) {
        return "agent_instruction"
    }
    if ($path.StartsWith(".codex/")) {
        return "local_agent_configuration"
    }
    if ($path.StartsWith(".github/")) {
        return "collaboration_configuration"
    }
    if ($path.StartsWith(".vscode/")) {
        return "editor_configuration"
    }
    if ($path -notmatch "/") {
        return "repository_root"
    }
    return "unclassified"
}

function Get-AuditDisposition {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Layer
    )

    switch ($Layer) {
        "dependency_environment" { return "structural_dependency_review" }
        "historical_backup" { return "provenance_duplicate_hygiene_review" }
        "temporary" { return "temporary_intake_review" }
        "archive" { return "archive_integrity_provenance_review" }
        "generated_artifact" { return "generated_evidence_integrity_review" }
        "vcs_metadata" { return "vcs_metadata_structural_review" }
        default { return "semantic_review_required" }
    }
}

function Test-TextCandidate {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    $extension = [IO.Path]::GetExtension($Path).ToLowerInvariant()
    $leaf = [IO.Path]::GetFileName($Path).ToLowerInvariant()
    if (
        $extension -in @(
            ".md", ".txt", ".luau", ".lua", ".ps1", ".psm1", ".py", ".json",
            ".jsonl", ".toml", ".yml", ".yaml", ".xml", ".csv", ".tsv", ".ini",
            ".cfg", ".conf", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx",
            ".html", ".css", ".scss", ".sql", ".sh", ".bat", ".cmd", ".gitignore",
            ".gitattributes", ".editorconfig"
        )
    ) {
        return $true
    }
    return $leaf -in @(
        "readme", "license", "copying", "notice", "agents.md", "dockerfile",
        "makefile"
    )
}

function Get-Sha256 {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    $stream = $null
    $algorithm = $null
    try {
        $stream = [IO.File]::Open(
            $Path,
            [IO.FileMode]::Open,
            [IO.FileAccess]::Read,
            [IO.FileShare]::ReadWrite
        )
        $algorithm = [Security.Cryptography.SHA256]::Create()
        $bytes = $algorithm.ComputeHash($stream)
        return ([BitConverter]::ToString($bytes) -replace "-", "").ToLowerInvariant()
    }
    finally {
        if ($algorithm) {
            $algorithm.Dispose()
        }
        if ($stream) {
            $stream.Dispose()
        }
    }
}

function Get-Utf8Status {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [Parameter(Mandatory = $true)]
        [long]$Length
    )

    if (-not (Test-TextCandidate -Path $Path)) {
        return "not_applicable"
    }
    if ($Length -gt 20MB) {
        return "deferred_large_text"
    }

    try {
        $encoding = [Text.UTF8Encoding]::new($false, $true)
        [void][IO.File]::ReadAllText($Path, $encoding)
        return "valid_utf8"
    }
    catch [Text.DecoderFallbackException] {
        return "invalid_utf8"
    }
}

$root = (Resolve-Path -LiteralPath $RepositoryRoot).Path
$output = [IO.Path]::GetFullPath($OutputDirectory)
if ($output.StartsWith(($root.TrimEnd("\") + "\"), [StringComparison]::OrdinalIgnoreCase)) {
    throw "OutputDirectory must stay outside the repository so the audit cannot inventory itself."
}

$git = Get-GitExecutable
$tracked = Get-StringSet -Values @(& $git -C $root ls-files)
$untracked = Get-StringSet -Values @(& $git -C $root ls-files --others --exclude-standard)
$ignored = Get-StringSet -Values @(& $git -C $root ls-files --others --ignored --exclude-standard)

[void](New-Item -ItemType Directory -Path $output -Force)

$ledgerPath = Join-Path $output "file-ledger.jsonl"
$duplicatePath = Join-Path $output "duplicate-groups.jsonl"
$summaryPath = Join-Path $output "summary.json"
$utf8 = [Text.UTF8Encoding]::new($false)
$ledgerWriter = [IO.StreamWriter]::new($ledgerPath, $false, $utf8)
$duplicateWriter = $null

$layerCounts = [Collections.Generic.Dictionary[string, int]]::new(
    [StringComparer]::OrdinalIgnoreCase
)
$gitCounts = [Collections.Generic.Dictionary[string, int]]::new(
    [StringComparer]::OrdinalIgnoreCase
)
$utf8Counts = [Collections.Generic.Dictionary[string, int]]::new(
    [StringComparer]::OrdinalIgnoreCase
)
$hashPaths = [Collections.Generic.Dictionary[string, Collections.Generic.List[string]]]::new(
    [StringComparer]::OrdinalIgnoreCase
)
$totalBytes = [long]0
$hashErrors = [Collections.Generic.List[object]]::new()
$caseMap = [Collections.Generic.Dictionary[string, Collections.Generic.List[string]]]::new(
    [StringComparer]::Ordinal
)

$filePaths = [Collections.Generic.List[string]]::new()
$directoryStack = [Collections.Generic.Stack[string]]::new()
$directoryStack.Push($root)
while ($directoryStack.Count -gt 0) {
    $directory = $directoryStack.Pop()
    foreach ($path in [IO.Directory]::EnumerateFiles($directory)) {
        $filePaths.Add($path)
    }
    foreach ($child in [IO.Directory]::EnumerateDirectories($directory)) {
        $childInfo = [IO.DirectoryInfo]::new($child)
        if ($childInfo.Attributes.HasFlag([IO.FileAttributes]::ReparsePoint)) {
            continue
        }
        if (
            -not $IncludeGitMetadata -and
            $childInfo.FullName.Equals(
                (Join-Path $root ".git"),
                [StringComparison]::OrdinalIgnoreCase
            )
        ) {
            continue
        }
        $directoryStack.Push($childInfo.FullName)
    }
}
$sortedFilePaths = $filePaths.ToArray()
[Array]::Sort($sortedFilePaths, [StringComparer]::OrdinalIgnoreCase)

try {
    $index = 0
    foreach ($fullPath in $sortedFilePaths) {
        $index++
        $file = [IO.FileInfo]::new($fullPath)
        $relative = $fullPath.Substring($root.TrimEnd("\").Length + 1) -replace "\\", "/"
        $layer = Get-RepositoryLayer -RelativePath $relative
        $disposition = Get-AuditDisposition -Layer $layer
        $gitStatus = if ($tracked.Contains($relative)) {
            "tracked"
        }
        elseif ($ignored.Contains($relative)) {
            "ignored"
        }
        elseif ($untracked.Contains($relative)) {
            "untracked"
        }
        else {
            "outside_git_inventory"
        }

        $hash = $null
        $hashStatus = "pass"
        try {
            $hash = Get-Sha256 -Path $file.FullName
        }
        catch {
            $hashStatus = "error"
            $hashErrors.Add([pscustomobject]@{
                    path = $relative
                    errorType = $_.Exception.GetType().FullName
                })
        }

        $utf8Status = Get-Utf8Status -Path $file.FullName -Length $file.Length
        $extension = [IO.Path]::GetExtension($relative).ToLowerInvariant()
        $totalBytes += $file.Length

        Add-Count -Dictionary $layerCounts -Key $layer
        Add-Count -Dictionary $gitCounts -Key $gitStatus
        Add-Count -Dictionary $utf8Counts -Key $utf8Status

        if ($hash) {
            if (-not $hashPaths.ContainsKey($hash)) {
                $hashPaths[$hash] = [Collections.Generic.List[string]]::new()
            }
            $hashPaths[$hash].Add($relative)
        }

        $caseKey = $relative.ToLowerInvariant()
        if (-not $caseMap.ContainsKey($caseKey)) {
            $caseMap[$caseKey] = [Collections.Generic.List[string]]::new()
        }
        $caseMap[$caseKey].Add($relative)

        $record = [ordered]@{
            path = $relative
            sizeBytes = $file.Length
            modifiedUtc = $file.LastWriteTimeUtc.ToString("o")
            extension = $extension
            sha256 = $hash
            hashStatus = $hashStatus
            gitStatus = $gitStatus
            layer = $layer
            disposition = $disposition
            utf8Status = $utf8Status
        }
        $ledgerWriter.WriteLine(($record | ConvertTo-Json -Compress -Depth 4))

        if (($index % 2000) -eq 0) {
            Write-Progress -Activity "Auditing repository files" `
                -Status "$index / $($sortedFilePaths.Count)" `
                -PercentComplete (($index / $sortedFilePaths.Count) * 100)
        }
    }
}
finally {
    $ledgerWriter.Dispose()
    Write-Progress -Activity "Auditing repository files" -Completed
}

$duplicateGroups = 0
$duplicateFiles = 0
$duplicateWriter = [IO.StreamWriter]::new($duplicatePath, $false, $utf8)
try {
    foreach ($hash in @($hashPaths.Keys | Sort-Object)) {
        $paths = @($hashPaths[$hash])
        if ($paths.Count -le 1) {
            continue
        }
        $duplicateGroups++
        $duplicateFiles += $paths.Count
        $duplicateWriter.WriteLine((
                [ordered]@{
                    sha256 = $hash
                    fileCount = $paths.Count
                    paths = @($paths | Sort-Object)
                } | ConvertTo-Json -Compress -Depth 5
            ))
    }
}
finally {
    $duplicateWriter.Dispose()
}

$caseConflicts = @(
    foreach ($caseKey in $caseMap.Keys) {
        $paths = @($caseMap[$caseKey])
        if ($paths.Count -gt 1) {
            [ordered]@{
                normalizedPath = $caseKey
                paths = @($paths | Sort-Object)
            }
        }
    }
)

$ledgerHash = Get-Sha256 -Path $ledgerPath
$duplicateLedgerHash = Get-Sha256 -Path $duplicatePath
$summary = [ordered]@{
    schemaVersion = 1
    repositoryRoot = $root
    generatedUtc = [DateTime]::UtcNow.ToString("o")
    gitExecutable = $git
    includeGitMetadata = [bool]$IncludeGitMetadata
    fileCount = $sortedFilePaths.Count
    totalBytes = $totalBytes
    ledger = [ordered]@{
        path = $ledgerPath
        sha256 = $ledgerHash
    }
    duplicateLedger = [ordered]@{
        path = $duplicatePath
        sha256 = $duplicateLedgerHash
    }
    counts = [ordered]@{
        byLayer = $layerCounts
        byGitStatus = $gitCounts
        byUtf8Status = $utf8Counts
    }
    duplicateGroups = $duplicateGroups
    filesInDuplicateGroups = $duplicateFiles
    hashErrors = $hashErrors
    caseConflicts = $caseConflicts
}
[IO.File]::WriteAllText(
    $summaryPath,
    ($summary | ConvertTo-Json -Depth 10),
    $utf8
)

Write-Output "PASS repository audit ledger"
Write-Output "Files: $($sortedFilePaths.Count)"
Write-Output "Bytes: $totalBytes"
Write-Output "Ledger: $ledgerPath"
Write-Output "Ledger SHA-256: $ledgerHash"
Write-Output "Summary: $summaryPath"
