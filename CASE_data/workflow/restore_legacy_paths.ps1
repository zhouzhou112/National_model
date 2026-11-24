# Optional compatibility setup after cloning. Never overwrites an existing real directory.
$ErrorActionPreference = 'Stop'
$taskRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$dataRoot = [IO.Path]::GetFullPath((Join-Path $taskRoot 'CASE_data')) + '\'
$registry = Get-Content -LiteralPath (Join-Path $taskRoot 'CASE_data\00_registry\path_migrations.json') -Raw | ConvertFrom-Json
foreach ($entry in $registry.moves) {
    $oldPath = [IO.Path]::GetFullPath((Join-Path $taskRoot $entry.source))
    $newPath = [IO.Path]::GetFullPath((Join-Path $taskRoot $entry.destination))
    if (-not $oldPath.StartsWith($taskRoot + '\',[StringComparison]::OrdinalIgnoreCase) -or -not $newPath.StartsWith($dataRoot,[StringComparison]::OrdinalIgnoreCase)) { throw 'Path outside workspace' }
    if (-not (Test-Path -LiteralPath $newPath)) { Write-Output "SKIP missing payload $newPath"; continue }
    if (Test-Path -LiteralPath $oldPath) { Write-Output "KEEP existing path $oldPath"; continue }
    $parent = [IO.Path]::GetDirectoryName($oldPath)
    if (-not (Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
    New-Item -ItemType Junction -Path $oldPath -Target $newPath | Out-Null
}
