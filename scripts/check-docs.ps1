[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repositoryRoot = [IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
$repositoryPrefix = $repositoryRoot.TrimEnd("\") + "\"
$strictUtf8 = [Text.UTF8Encoding]::new($false, $true)
$errors = [Collections.Generic.List[string]]::new()
$documents = [Collections.Generic.Dictionary[string, object]]::new(
    [StringComparer]::OrdinalIgnoreCase
)
$headingAnchors = [Collections.Generic.Dictionary[string, object]]::new(
    [StringComparer]::OrdinalIgnoreCase
)

function Add-DocumentationError {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Message
    )

    $errors.Add($Message)
}

function Get-RepositoryRelativePath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    $fullPath = [IO.Path]::GetFullPath($Path)
    if ($fullPath.Equals($repositoryRoot, [StringComparison]::OrdinalIgnoreCase)) {
        return "."
    }
    if (-not $fullPath.StartsWith($repositoryPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        return $fullPath
    }

    return $fullPath.Substring($repositoryPrefix.Length).Replace("\", "/")
}

function ConvertTo-MarkdownAnchor {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Heading
    )

    $value = [regex]::Replace($Heading, "\[([^\]]+)\]\([^)]+\)", '$1')
    $value = $value.Replace('`', "").Replace("*", "").Replace("_", "")
    $value = $value.Trim().ToLowerInvariant()
    $builder = [Text.StringBuilder]::new()

    foreach ($character in $value.ToCharArray()) {
        if ([char]::IsLetterOrDigit($character) -or $character -eq "-" -or $character -eq "_") {
            [void]$builder.Append($character)
        }
        elseif ([char]::IsWhiteSpace($character)) {
            [void]$builder.Append("-")
        }
    }

    return ([regex]::Replace($builder.ToString(), "-+", "-")).Trim("-")
}

function Get-LinkDestination {
    param(
        [Parameter(Mandatory = $true)]
        [string]$SourcePath,
        [Parameter(Mandatory = $true)]
        [string]$RawTarget,
        [switch]$ReportErrors
    )

    $target = $RawTarget.Trim()
    if ($target.StartsWith("<")) {
        $closingBracket = $target.IndexOf(">")
        if ($closingBracket -lt 1) {
            if ($ReportErrors) {
                Add-DocumentationError "$(Get-RepositoryRelativePath $SourcePath): malformed angle-bracket link '$RawTarget'."
            }
            return $null
        }
        $target = $target.Substring(1, $closingBracket - 1)
    }
    else {
        $whitespaceIndex = $target.IndexOfAny([char[]]@(" ", "`t"))
        if ($whitespaceIndex -ge 0) {
            $target = $target.Substring(0, $whitespaceIndex)
        }
    }

    if ($target -match "^(?i:https?|mailto|tel):") {
        return $null
    }

    $fragment = ""
    $fragmentIndex = $target.IndexOf("#")
    if ($fragmentIndex -ge 0) {
        $fragment = [uri]::UnescapeDataString($target.Substring($fragmentIndex + 1))
        $target = $target.Substring(0, $fragmentIndex)
    }

    if ([string]::IsNullOrWhiteSpace($target)) {
        return [pscustomobject]@{
            Path = [IO.Path]::GetFullPath($SourcePath)
            Fragment = $fragment
        }
    }

    if ($target.StartsWith("/") -or $target.StartsWith("\") -or $target -match "^[A-Za-z]:") {
        if ($ReportErrors) {
            Add-DocumentationError "$(Get-RepositoryRelativePath $SourcePath): repository link must be relative, got '$RawTarget'."
        }
        return $null
    }

    try {
        $decodedTarget = [uri]::UnescapeDataString($target).Replace("/", "\")
        $destination = [IO.Path]::GetFullPath(
            (Join-Path (Split-Path -Parent $SourcePath) $decodedTarget)
        )
    }
    catch {
        if ($ReportErrors) {
            Add-DocumentationError "$(Get-RepositoryRelativePath $SourcePath): invalid relative link '$RawTarget'."
        }
        return $null
    }

    if (-not $destination.StartsWith($repositoryPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        if ($ReportErrors) {
            Add-DocumentationError "$(Get-RepositoryRelativePath $SourcePath): link escapes the repository: '$RawTarget'."
        }
        return $null
    }
    if (-not (Test-Path -LiteralPath $destination)) {
        if ($ReportErrors) {
            Add-DocumentationError "$(Get-RepositoryRelativePath $SourcePath): missing relative link target '$RawTarget'."
        }
        return $null
    }

    return [pscustomobject]@{
        Path = $destination
        Fragment = $fragment
    }
}

function Get-MetadataFields {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Text
    )

    $fields = [Collections.Generic.Dictionary[string, string]]::new(
        [StringComparer]::OrdinalIgnoreCase
    )
    $lines = [regex]::Split($Text, "\r?\n")
    $insideMetadata = $false
    $sawDataRow = $false

    foreach ($line in $lines) {
        if (-not $insideMetadata) {
            if ($line -match "^\|\s*Champ\s*\|\s*Valeur\s*\|\s*$") {
                $insideMetadata = $true
            }
            continue
        }

        if ($line -match "^\|\s*-+\s*\|\s*-+\s*\|\s*$") {
            continue
        }
        if ($line -match "^\|\s*(?<field>[^|]+?)\s*\|\s*(?<value>.*?)\s*\|\s*$") {
            $field = $Matches.field.Trim()
            $value = $Matches.value.Trim()
            if (-not $fields.ContainsKey($field)) {
                $fields.Add($field, $value)
            }
            $sawDataRow = $true
            continue
        }
        if ($sawDataRow) {
            break
        }
    }

    return $fields
}

function Test-Metadata {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [Parameter(Mandatory = $true)]
        [string]$ExpectedClass
    )

    $fullPath = [IO.Path]::GetFullPath($Path)
    if (-not $documents.ContainsKey($fullPath)) {
        Add-DocumentationError "$(Get-RepositoryRelativePath $fullPath): metadata target was not loaded."
        return
    }

    $fields = Get-MetadataFields -Text $documents[$fullPath].Text
    $relativePath = Get-RepositoryRelativePath $fullPath
    $proprietaire = "Propri" + [char]0x00E9 + "taire"
    $portee = "Port" + [char]0x00E9 + "e"
    $derniereRevue = "Derni" + [char]0x00E8 + "re revue"
    $requiredFieldGroups = @(
        @("ID"),
        @("Classe"),
        @("Cycle de vie"),
        @($proprietaire, "$proprietaire / approbateur"),
        @("Scope", $portee),
        @("Source", "Sources", "Remplace"),
        @($derniereRevue),
        @("Revue suivante")
    )

    if ($ExpectedClass -in @("CONTRACT", "CANON", "CONFIG", "HYPOTHESIS")) {
        $requiredFieldGroups += ,@("Version")
    }
    if ($ExpectedClass -eq "EVIDENCE") {
        $requiredFieldGroups += ,@("Date", "Date de preuve")
    }

    foreach ($alternatives in $requiredFieldGroups) {
        $found = $false
        foreach ($fieldName in $alternatives) {
            if ($fields.ContainsKey($fieldName) -and
                -not [string]::IsNullOrWhiteSpace($fields[$fieldName])) {
                $found = $true
                break
            }
        }
        if (-not $found) {
            Add-DocumentationError "${relativePath}: missing metadata field $($alternatives -join ' or ')."
        }
    }

    if ($fields.ContainsKey("Classe") -and
        $fields["Classe"] -notmatch [regex]::Escape($ExpectedClass)) {
        Add-DocumentationError (
            "${relativePath}: metadata class '$($fields["Classe"])' does not " +
            "contain registered class '$ExpectedClass'."
        )
    }
}

$markdownPaths = [Collections.Generic.List[string]]::new()
foreach ($rootDocument in @(
    "AGENTS.md",
    "README.md",
    "Roblox_Top_1_Game_Design_Document_v1.0.md",
    "studio\README.md",
    ".github\pull_request_template.md"
)) {
    $candidate = Join-Path $repositoryRoot $rootDocument
    if (Test-Path -LiteralPath $candidate -PathType Leaf) {
        $markdownPaths.Add([IO.Path]::GetFullPath($candidate))
    }
}
foreach ($directory in @("docs", "plans")) {
    $fullDirectory = Join-Path $repositoryRoot $directory
    if (Test-Path -LiteralPath $fullDirectory -PathType Container) {
        Get-ChildItem -LiteralPath $fullDirectory -Filter "*.md" -File -Recurse |
            ForEach-Object { $markdownPaths.Add($_.FullName) }
    }
}

$markdownPaths = @($markdownPaths | Sort-Object -Unique)
foreach ($path in $markdownPaths) {
    try {
        $text = $strictUtf8.GetString([IO.File]::ReadAllBytes($path))
    }
    catch [Text.DecoderFallbackException] {
        Add-DocumentationError "$(Get-RepositoryRelativePath $path): invalid UTF-8."
        continue
    }

    $outsideFenceLines = [Collections.Generic.List[object]]::new()
    $fenceCharacter = $null
    $fenceLength = 0
    $lines = [regex]::Split($text, "\r?\n")

    for ($index = 0; $index -lt $lines.Count; $index++) {
        $line = $lines[$index]
        if ($line -match '^\s*(?<marker>`{3,}|~{3,})') {
            $marker = $Matches.marker
            if ($null -eq $fenceCharacter) {
                $fenceCharacter = $marker.Substring(0, 1)
                $fenceLength = $marker.Length
            }
            elseif ($marker.Substring(0, 1) -eq $fenceCharacter -and
                $marker.Length -ge $fenceLength) {
                $fenceCharacter = $null
                $fenceLength = 0
            }
            continue
        }
        if ($null -eq $fenceCharacter) {
            $outsideFenceLines.Add([pscustomobject]@{
                Number = $index + 1
                Text = $line
            })
        }
    }

    if ($null -ne $fenceCharacter) {
        Add-DocumentationError "$(Get-RepositoryRelativePath $path): unclosed Markdown fence."
    }

    $seenHeadings = [Collections.Generic.Dictionary[string, int]]::new(
        [StringComparer]::OrdinalIgnoreCase
    )
    $anchors = [Collections.Generic.HashSet[string]]::new(
        [StringComparer]::OrdinalIgnoreCase
    )
    foreach ($lineInfo in $outsideFenceLines) {
        if ($lineInfo.Text -notmatch "^#{1,6}\s+(?<heading>.+?)\s*$") {
            continue
        }

        $heading = [regex]::Replace($Matches.heading, "\s+#+\s*$", "").Trim()
        $normalizedHeading = [regex]::Replace(
            $heading.Replace('`', "").Replace("*", "").Replace("_", ""),
            "\s+",
            " "
        ).Trim()
        if ($seenHeadings.ContainsKey($normalizedHeading)) {
            Add-DocumentationError (
                "$(Get-RepositoryRelativePath $path): duplicate heading '$heading' " +
                "at lines $($seenHeadings[$normalizedHeading]) and $($lineInfo.Number)."
            )
        }
        else {
            $seenHeadings.Add($normalizedHeading, $lineInfo.Number)
        }

        $anchor = ConvertTo-MarkdownAnchor -Heading $heading
        if (-not [string]::IsNullOrWhiteSpace($anchor)) {
            [void]$anchors.Add($anchor)
        }
    }

    $documents.Add($path, [pscustomobject]@{
        Text = $text
        Lines = $outsideFenceLines
    })
    $headingAnchors.Add($path, $anchors)
}

foreach ($path in $markdownPaths) {
    if (-not $documents.ContainsKey($path)) {
        continue
    }

    foreach ($lineInfo in $documents[$path].Lines) {
        foreach ($match in [regex]::Matches(
            $lineInfo.Text,
            "!?\[[^\]]*\]\((?<target>[^)]+)\)"
        )) {
            $rawTarget = $match.Groups["target"].Value
            $destination = Get-LinkDestination `
                -SourcePath $path `
                -RawTarget $rawTarget `
                -ReportErrors
            if ($null -eq $destination -or [string]::IsNullOrWhiteSpace($destination.Fragment)) {
                continue
            }
            if ((Test-Path -LiteralPath $destination.Path -PathType Leaf) -and
                [IO.Path]::GetExtension($destination.Path) -eq ".md") {
                if (-not $headingAnchors.ContainsKey($destination.Path) -or
                    -not $headingAnchors[$destination.Path].Contains($destination.Fragment)) {
                    Add-DocumentationError (
                        "$(Get-RepositoryRelativePath $path):$($lineInfo.Number): " +
                        "missing Markdown anchor '#$($destination.Fragment)' in " +
                        "$(Get-RepositoryRelativePath $destination.Path)."
                    )
                }
            }
        }
    }
}

$registerPath = [IO.Path]::GetFullPath(
    (Join-Path $repositoryRoot "docs\00-governance\DOCUMENT_REGISTER.md")
)
if (-not $documents.ContainsKey($registerPath)) {
    Add-DocumentationError "docs/00-governance/DOCUMENT_REGISTER.md: register is missing."
}
else {
    $registeredPaths = [Collections.Generic.HashSet[string]]::new(
        [StringComparer]::OrdinalIgnoreCase
    )
    foreach ($match in [regex]::Matches(
        $documents[$registerPath].Text,
        "\[[^\]]+\]\((?<target>[^)]+)\)"
    )) {
        $destination = Get-LinkDestination `
            -SourcePath $registerPath `
            -RawTarget $match.Groups["target"].Value
        if ($null -ne $destination) {
            [void]$registeredPaths.Add([IO.Path]::GetFullPath($destination.Path))
        }
    }

    foreach ($path in $markdownPaths) {
        if ($path.Equals($registerPath, [StringComparison]::OrdinalIgnoreCase)) {
            continue
        }
        if (-not $registeredPaths.Contains($path)) {
            Add-DocumentationError "$(Get-RepositoryRelativePath $path): durable Markdown file is absent from DOCUMENT_REGISTER.md."
        }
    }

    $seenRegisterIds = [Collections.Generic.Dictionary[string, int]]::new(
        [StringComparer]::OrdinalIgnoreCase
    )
    $registerLines = [regex]::Split($documents[$registerPath].Text, "\r?\n")
    for ($index = 0; $index -lt $registerLines.Count; $index++) {
        if ($registerLines[$index] -notmatch '^\|\s*`(?<id>[A-Z0-9][A-Z0-9-]+)`\s*\|') {
            continue
        }
        $id = $Matches.id
        if ($seenRegisterIds.ContainsKey($id)) {
            Add-DocumentationError "docs/00-governance/DOCUMENT_REGISTER.md: duplicate ID '$id' at lines $($seenRegisterIds[$id]) and $($index + 1)."
        }
        else {
            $seenRegisterIds.Add($id, $index + 1)
        }
    }

    # These paths are deliberately excluded from the modern metadata schema.
    # The reasons are emitted so an exclusion can never look like a passing check.
    $metadataExclusions = @{
        "AGENTS.md" = "execution constitution with an externally mandated format"
        "docs/DEFENSE_LOOP_0_1.md" = "superseded pre-ADR contract preserved as history"
        "docs/DEFENSE_LOOP_0_2.md" = "accepted pre-ADR baseline; registry supplies its migration metadata"
        "docs/ROBLOX_3D_ASSET_WORKFLOW.md" = "3D contract metadata migration is owned by the active 3D audit"
        "docs/BLENDER_MCP_WORKBENCH.md" = "3D contract metadata migration is owned by the active 3D audit"
        "docs/evidence/BLENDER_WORKBENCH_VERTICAL_SLICE_2026-07-17.md" = "RECORDED 3D evidence; only a 3D addendum may alter its metadata"
        "docs/references/TMP_DOCS_INTAKE_2026-07-15.md" = "RECORDED intake evidence preserved without rewriting history"
    }
    $usedMetadataExclusions = [Collections.Generic.HashSet[string]]::new(
        [StringComparer]::OrdinalIgnoreCase
    )
    $metadataClasses = @("CONTRACT", "CANON", "CONFIG", "HYPOTHESIS", "EVIDENCE")
    for ($index = 0; $index -lt $registerLines.Count; $index++) {
        $line = $registerLines[$index]
        if ($line -notmatch (
            '^\|\s*`(?<id>[A-Z0-9][A-Z0-9-]+)`\s*\|\s*' +
            '\[[^\]]+\]\((?<target>[^)]+)\)\s*\|\s*`(?<class>[^`]+)`\s*\|'
        )) {
            continue
        }

        $registeredClass = $Matches.class
        if ($registeredClass -notin $metadataClasses) {
            continue
        }
        $destination = Get-LinkDestination `
            -SourcePath $registerPath `
            -RawTarget $Matches.target
        if ($null -eq $destination) {
            continue
        }
        $relativePath = Get-RepositoryRelativePath $destination.Path
        if ($metadataExclusions.ContainsKey($relativePath)) {
            [void]$usedMetadataExclusions.Add($relativePath)
            Write-Output "SKIP metadata $relativePath -- $($metadataExclusions[$relativePath])"
            continue
        }

        Test-Metadata -Path $destination.Path -ExpectedClass $registeredClass
    }

    foreach ($excludedPath in $metadataExclusions.Keys) {
        $fullExcludedPath = Join-Path $repositoryRoot $excludedPath.Replace("/", "\")
        if (-not (Test-Path -LiteralPath $fullExcludedPath -PathType Leaf)) {
            Add-DocumentationError "Stale metadata exclusion points to missing file: $excludedPath."
        }
        elseif (-not $usedMetadataExclusions.Contains($excludedPath)) {
            Add-DocumentationError "Metadata exclusion is no longer used by the register: $excludedPath."
        }
    }
}

foreach ($template in @(
    @{ Path = "docs\templates\ADR_TEMPLATE.md"; Class = "CONTRACT" },
    @{ Path = "docs\templates\EVIDENCE_REPORT_TEMPLATE.md"; Class = "EVIDENCE" },
    @{ Path = "docs\templates\EXPERIMENT_BRIEF_TEMPLATE.md"; Class = "HYPOTHESIS" },
    @{ Path = "docs\templates\SYSTEM_SPEC_TEMPLATE.md"; Class = "CONTRACT" }
)) {
    Test-Metadata `
        -Path (Join-Path $repositoryRoot $template.Path) `
        -ExpectedClass $template.Class
}

$productRegisterPath = [IO.Path]::GetFullPath(
    (Join-Path $repositoryRoot "docs\00-governance\PRODUCT_DEFINITION_REGISTER.md")
)
if ($documents.ContainsKey($productRegisterPath)) {
    $definitionStates = @(
        "DEFINED_ACCEPTED",
        "SPECIFIED_IN_REVIEW",
        "OPEN",
        "DEFERRED_BY_GATE",
        "OPTIONAL_DECISION",
        "REJECTED"
    )
    $implementationStates = @("NOT_STARTED", "PARTIAL", "IMPLEMENTED", "NOT_APPLICABLE")
    $proofStates = @("PASS", "FAIL", "PARTIAL", "BLOCKED", "UNKNOWN")
    $seenProductIds = [Collections.Generic.HashSet[int]]::new()

    foreach ($lineInfo in $documents[$productRegisterPath].Lines) {
        if ($lineInfo.Text -notmatch '^\|\s*`PD-(?<number>\d{2})`\s*\|') {
            continue
        }
        $cells = @($lineInfo.Text.Trim().Trim("|").Split("|") | ForEach-Object { $_.Trim() })
        if ($cells.Count -ne 7) {
            Add-DocumentationError "docs/00-governance/PRODUCT_DEFINITION_REGISTER.md:$($lineInfo.Number): product status row must have 7 cells."
            continue
        }

        $number = [int]$Matches.number
        if (-not $seenProductIds.Add($number)) {
            Add-DocumentationError "docs/00-governance/PRODUCT_DEFINITION_REGISTER.md:$($lineInfo.Number): duplicate PD-$('{0:D2}' -f $number)."
        }

        foreach ($statusCheck in @(
            @{ Cell = $cells[2]; Allowed = $definitionStates; Name = "definition" },
            @{ Cell = $cells[3]; Allowed = $implementationStates; Name = "implementation" },
            @{ Cell = $cells[4]; Allowed = $proofStates; Name = "proof" }
        )) {
            if ($statusCheck.Cell -notmatch '^`(?<token>[A-Z_]+)`$' -or
                $Matches.token -notin $statusCheck.Allowed) {
                Add-DocumentationError (
                    "docs/00-governance/PRODUCT_DEFINITION_REGISTER.md:$($lineInfo.Number): " +
                    "$($statusCheck.Name) cell '$($statusCheck.Cell)' is not an exact controlled token."
                )
            }
        }
    }

    $expectedProductIds = @(1..28)
    $missingProductIds = @($expectedProductIds | Where-Object { -not $seenProductIds.Contains($_) })
    if ($missingProductIds.Count -gt 0) {
        Add-DocumentationError "Product register is missing IDs: $($missingProductIds -join ', ')."
    }
}

if ($errors.Count -gt 0) {
    foreach ($documentationError in $errors) {
        Write-Output "FAIL $documentationError"
    }
    throw "Documentation checks failed with $($errors.Count) error(s)."
}

Write-Output "PASS documentation corpus ($($markdownPaths.Count) Markdown files)"
