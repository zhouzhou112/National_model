$ErrorActionPreference = 'Stop'
$taskRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..'))
$caseRoot = [IO.Path]::GetFullPath((Join-Path $taskRoot 'case_results')) + '\'
$targetRoot = [IO.Path]::GetFullPath((Join-Path $taskRoot 'CASE_data\03_legacy_deliveries')) + '\'
$plan = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'move_plan.json') -Raw | ConvertFrom-Json
$compatibilityFiles = [Collections.Generic.List[object]]::new()
function Add-CompatibilityTree([string]$oldDir,[string]$newDir) {
    if (-not (Test-Path -LiteralPath $oldDir)) { New-Item -ItemType Junction -Path $oldDir -Target $newDir | Out-Null; return }
    $item = Get-Item -LiteralPath $oldDir
    if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { return }
    foreach ($child in Get-ChildItem -LiteralPath $newDir -Force) {
        $oldChild = Join-Path $oldDir $child.Name
        if ($child.PSIsContainer) { Add-CompatibilityTree $oldChild $child.FullName }
        elseif (-not (Test-Path -LiteralPath $oldChild)) {
            if ($child.Name -ne 'README.md' -or $child.Length -gt 100KB) { throw "Non-navigation file needs compatibility decision: $oldChild" }
            # Only tiny historical navigation cards may be copied into locked empty folders.
            Copy-Item -LiteralPath $child.FullName -Destination $oldChild
            $compatibilityFiles.Add([pscustomobject]@{path=$oldChild;source=$child.FullName;bytes=$child.Length;reason='Locked empty navigation directory; original card preserved in CASE_data'})
        }
    }
}
foreach ($entry in $plan.moves | Where-Object { $_.source.StartsWith('case_results/') }) {
    $source = [IO.Path]::GetFullPath((Join-Path $taskRoot $entry.source))
    $target = [IO.Path]::GetFullPath((Join-Path $taskRoot $entry.destination))
    if (-not $source.StartsWith($caseRoot,[StringComparison]::OrdinalIgnoreCase)) { throw 'Source outside case_results' }
    if (-not $target.StartsWith($targetRoot,[StringComparison]::OrdinalIgnoreCase)) { throw 'Target outside archive root' }
    $current = Get-Item -LiteralPath $source
    if ($current.Attributes -band [IO.FileAttributes]::ReparsePoint) {
        if ([IO.Path]::GetFullPath($current.Target) -ne $target) { throw 'Wrong existing junction' }
        continue
    }
    foreach ($member in $plan.files | Where-Object { $_.path.StartsWith($entry.source + '/') }) {
        $from = [IO.Path]::GetFullPath((Join-Path $taskRoot $member.path))
        $to = [IO.Path]::GetFullPath((Join-Path $taskRoot $member.destination))
        if (-not $from.StartsWith($source + '\',[StringComparison]::OrdinalIgnoreCase) -or -not $to.StartsWith($target + '\',[StringComparison]::OrdinalIgnoreCase)) { throw 'File outside approved subtree' }
        if (Test-Path -LiteralPath $to) {
            if (Test-Path -LiteralPath $from) { throw "Both copies present, no overwrite: $from" }
            if ((Get-Item -LiteralPath $to).Length -ne $member.bytes) { throw 'Existing target size differs' }
            continue
        }
        $parent = [IO.Path]::GetDirectoryName($to)
        if (-not (Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
        Move-Item -LiteralPath $from -Destination $to
    }
    # Remove only now-empty containers; no recursive deletion and no data deletion.
    $emptyCandidates = @(Get-ChildItem -LiteralPath $source -Directory -Recurse -Force | Sort-Object { $_.FullName.Length } -Descending)
    foreach ($dir in $emptyCandidates) {
        if (-not $dir.FullName.StartsWith($source + '\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Container escaped source' }
        if (@(Get-ChildItem -LiteralPath $dir.FullName -Force).Count -eq 0) {
            try { Remove-Item -LiteralPath $dir.FullName -Force } catch [System.IO.IOException] { Write-Output "EMPTY_LOCKED $($dir.FullName)" }
        }
    }
    if (@(Get-ChildItem -LiteralPath $source -Force).Count -eq 0) {
        try { Remove-Item -LiteralPath $source -Force } catch [System.IO.IOException] { Write-Output "EMPTY_LOCKED $source" }
    }
    Add-CompatibilityTree $source $target
    Write-Output "MOVED_AND_LINKED $($entry.source)"
}
$compatibilityFiles | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'locked_navigation_cards.json') -Encoding utf8
