$ErrorActionPreference = 'Stop'
$taskRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..'))
$dataRoot = [IO.Path]::GetFullPath((Join-Path $taskRoot 'CASE_data'))
$plan = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'move_plan.json') -Raw | ConvertFrom-Json
$hashes = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'hashes_before.json') -Raw | ConvertFrom-Json
if ($hashes.status -ne 'PASS' -or $hashes.file_count -ne $plan.files.Count) { throw 'Pre-move hashes incomplete' }
$receipts = [Collections.Generic.List[object]]::new()
foreach ($item in $plan.moves) {
    $source = [IO.Path]::GetFullPath((Join-Path $taskRoot $item.source))
    $target = [IO.Path]::GetFullPath((Join-Path $taskRoot $item.destination))
    $reviewsRoot = [IO.Path]::GetFullPath((Join-Path $taskRoot 'supplementary_materials\reviews')) + '\'
    $casesRoot = [IO.Path]::GetFullPath((Join-Path $taskRoot 'case_results')) + '\'
    if (-not ($source.StartsWith($reviewsRoot,[StringComparison]::OrdinalIgnoreCase) -or $source.StartsWith($casesRoot,[StringComparison]::OrdinalIgnoreCase))) { throw "Invalid source: $source" }
    if (-not $target.StartsWith($dataRoot + '\',[StringComparison]::OrdinalIgnoreCase)) { throw "Invalid destination: $target" }
    if ((Test-Path -LiteralPath $source) -and (Test-Path -LiteralPath $target)) {
        $existing = Get-Item -LiteralPath $source
        if (-not ($existing.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw "Both real directories exist: $source" }
        if ([IO.Path]::GetFullPath($existing.Target) -ne $target) { throw "Wrong existing junction: $source" }
        $receipts.Add([pscustomobject]@{source=$source;destination=$target;status='MOVED';compatibility='NTFS_JUNCTION';utc=[DateTime]::UtcNow.ToString('o')})
        continue
    }
    if ([IO.Path]::GetPathRoot($source) -ne [IO.Path]::GetPathRoot($target)) { throw 'Only same-volume atomic moves allowed' }
    $parent = [IO.Path]::GetDirectoryName($target)
    if (-not (Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
    if (-not (Test-Path -LiteralPath $target)) {
        $sourceItem = Get-Item -LiteralPath $source
        if ($sourceItem.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Unexpected source link: $source" }
        Move-Item -LiteralPath $source -Destination $target
    } else {
        # Resume only a completed directory move whose compatibility link was blocked.
        $members = @($plan.files | Where-Object { $_.path.StartsWith($item.source + '/') })
        foreach ($member in $members) {
            $file = Get-Item -LiteralPath ([IO.Path]::GetFullPath((Join-Path $taskRoot $member.destination)))
            if ($file.Length -ne $member.bytes) { throw "Partial move differs: $($file.FullName)" }
        }
    }
    New-Item -ItemType Junction -Path $source -Target $target | Out-Null
    $link = Get-Item -LiteralPath $source
    if (-not ($link.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw "Compatibility link missing: $source" }
    $receipts.Add([pscustomobject]@{source=$source;destination=$target;status='MOVED';compatibility='NTFS_JUNCTION';utc=[DateTime]::UtcNow.ToString('o')})
    $receipts | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'moves_receipt.json') -Encoding utf8
    Write-Output "MOVED $($item.source)"
}
Write-Output "COMPLETE $($receipts.Count) directory moves; no deletions"
