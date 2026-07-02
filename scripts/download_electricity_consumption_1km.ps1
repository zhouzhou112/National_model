[CmdletBinding()]
param(
    [string]$OutputDir,
    [switch]$Extract,
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($OutputDir)) {
    $OutputDir = Join-Path $PSScriptRoot '..\data\raw\electricity_consumption_1km_2012_2019\source'
}

$files = @(
    [pscustomobject]@{
        Name = 'China_280_cities.csv'
        Url = 'https://ndownloader.figshare.com/files/45008041'
        Size = [int64]3105
        Md5 = 'dca30afc3111109b2e72c501381c151a'
    },
    [pscustomobject]@{
        Name = 'China_1km_Ele_201204_201912.zip'
        Url = 'https://ndownloader.figshare.com/files/45007633'
        Size = [int64]198361539
        Md5 = '87cdc40f0f5c644566c2506c238fc9fc'
    }
)

function Test-ExpectedFile {
    param(
        [Parameter(Mandatory)] [string]$Path,
        [Parameter(Mandatory)] [int64]$ExpectedSize,
        [Parameter(Mandatory)] [string]$ExpectedMd5
    )

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        return $false
    }
    if ((Get-Item -LiteralPath $Path).Length -ne $ExpectedSize) {
        return $false
    }
    $actualMd5 = (Get-FileHash -LiteralPath $Path -Algorithm MD5).Hash.ToLowerInvariant()
    return $actualMd5 -eq $ExpectedMd5.ToLowerInvariant()
}

function Invoke-VerifiedDownload {
    param(
        [Parameter(Mandatory)] $Spec,
        [Parameter(Mandatory)] [string]$Directory
    )

    $destination = Join-Path $Directory $Spec.Name
    if (Test-ExpectedFile -Path $destination -ExpectedSize $Spec.Size -ExpectedMd5 $Spec.Md5) {
        Write-Host "PASS existing: $destination"
        return
    }

    $timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
    $temporary = "$destination.partial_$timestamp"
    Write-Host "Downloading $($Spec.Url)"
    Write-Host "Temporary file: $temporary"

    Add-Type -AssemblyName System.Net.Http
    $client = [System.Net.Http.HttpClient]::new()
    $client.Timeout = [TimeSpan]::FromMinutes(30)
    try {
        $response = $client.GetAsync(
            $Spec.Url,
            [System.Net.Http.HttpCompletionOption]::ResponseHeadersRead
        ).GetAwaiter().GetResult()
        $response.EnsureSuccessStatusCode()
        $inputStream = $response.Content.ReadAsStreamAsync().GetAwaiter().GetResult()
        $outputStream = [System.IO.File]::Open(
            $temporary,
            [System.IO.FileMode]::CreateNew,
            [System.IO.FileAccess]::Write,
            [System.IO.FileShare]::None
        )
        try {
            $inputStream.CopyToAsync($outputStream).GetAwaiter().GetResult()
        }
        finally {
            $outputStream.Dispose()
            $inputStream.Dispose()
            $response.Dispose()
        }
    }
    finally {
        $client.Dispose()
    }

    if (-not (Test-ExpectedFile -Path $temporary -ExpectedSize $Spec.Size -ExpectedMd5 $Spec.Md5)) {
        $actualSize = (Get-Item -LiteralPath $temporary).Length
        $actualMd5 = (Get-FileHash -LiteralPath $temporary -Algorithm MD5).Hash.ToLowerInvariant()
        throw "Integrity check failed for $temporary (size=$actualSize, md5=$actualMd5). The partial file was retained."
    }

    if (Test-Path -LiteralPath $destination) {
        $invalidPath = "$destination.invalid_$timestamp"
        Move-Item -LiteralPath $destination -Destination $invalidPath
        Write-Warning "Existing invalid file retained as $invalidPath"
    }
    Move-Item -LiteralPath $temporary -Destination $destination
    Write-Host "PASS downloaded: $destination"
}

$resolvedOutputDir = [System.IO.Path]::GetFullPath($OutputDir)
if ($DryRun) {
    Write-Host "Output directory: $resolvedOutputDir"
    foreach ($spec in $files) {
        Write-Host "$($spec.Name) | $($spec.Size) bytes | MD5 $($spec.Md5) | $($spec.Url)"
    }
    Write-Host "Extract requested: $Extract"
    exit 0
}

New-Item -ItemType Directory -Force -Path $resolvedOutputDir | Out-Null
foreach ($spec in $files) {
    Invoke-VerifiedDownload -Spec $spec -Directory $resolvedOutputDir
}

if ($Extract) {
    $zipPath = Join-Path $resolvedOutputDir 'China_1km_Ele_201204_201912.zip'
    $extractDir = Join-Path (Split-Path $resolvedOutputDir -Parent) 'extracted'
    if (-not (Test-ExpectedFile -Path $zipPath -ExpectedSize 198361539 -ExpectedMd5 '87cdc40f0f5c644566c2506c238fc9fc')) {
        throw "Extraction refused because the ZIP has not passed integrity checks: $zipPath"
    }
    New-Item -ItemType Directory -Force -Path $extractDir | Out-Null
    Expand-Archive -LiteralPath $zipPath -DestinationPath $extractDir -Force
    $tifCount = (Get-ChildItem -LiteralPath $extractDir -Recurse -File -Filter '*.tif').Count
    if ($tifCount -ne 93) {
        throw "Expected 93 GeoTIFFs after extraction, found $tifCount in $extractDir"
    }
    Write-Host "PASS extracted 93 GeoTIFFs: $extractDir"
}
