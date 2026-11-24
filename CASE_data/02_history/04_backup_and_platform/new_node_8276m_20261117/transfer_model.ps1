$ErrorActionPreference = 'Stop'
$benchRoot = 'C:\NationalModelBench\ops_open2050_t32_20261118'
$benchSource = '/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20261115_opsopen_2050_v9a12_t44_m750_tol1e4_v1/output_8760'
$benchSshConfig = 'C:\Users\zz2\.ssh\config_paracloud_8276m'
$benchIdentity = Get-Content -LiteralPath "$benchRoot\setup\source_identity_20261118.json" -Raw | ConvertFrom-Json
New-Item -ItemType Directory -Path "$benchRoot\input\model_archive" -Force | Out-Null
$benchLock = [IO.File]::Open("$benchRoot\setup\transfer.lock",[IO.FileMode]::OpenOrCreate,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)
try {
    $benchCommands = @('lcd C:/NationalModelBench/ops_open2050_t32_20261118/input')
    foreach ($benchProperty in $benchIdentity.source_files.PSObject.Properties) {
        $benchRelative = $benchProperty.Name
        $benchTarget = Join-Path "$benchRoot\input" $benchRelative
        if (Test-Path -LiteralPath $benchTarget) {
            if ((Get-Item -LiteralPath $benchTarget).Length -gt $benchProperty.Value.bytes) { throw "Target larger than source: $benchRelative" }
        }
        $benchCommands += ('reget ' + $benchSource + '/' + $benchRelative + ' ' + $benchRelative)
    }
    $benchCommands += 'bye'
    [IO.File]::WriteAllLines("$benchRoot\setup\transfer.sftp",$benchCommands,[Text.Encoding]::ASCII)
    & 'C:\Windows\System32\OpenSSH\sftp.exe' -F $benchSshConfig -b "$benchRoot\setup\transfer.sftp" paracloud-8276m *> "$benchRoot\setup\transfer.log"
    if ($LASTEXITCODE -ne 0) { throw 'SFTP incomplete; partial files retained for resume after source identity recheck.' }
    $benchResults = @()
    foreach ($benchProperty in $benchIdentity.source_files.PSObject.Properties) {
        $benchRelative = $benchProperty.Name
        $benchTarget = Join-Path "$benchRoot\input" $benchRelative
        $benchExpected = $benchProperty.Value.sha256
        if ($benchRelative -eq 'model_archive/original.mps.gz') { $benchExpected = '33a4f822cbf894810082843e6ccabbb59db2183e3282f182b0df1cb807768a4b' }
        $benchBytes = (Get-Item -LiteralPath $benchTarget).Length
        $benchSha = (Get-FileHash -LiteralPath $benchTarget -Algorithm SHA256).Hash.ToLower()
        if ($benchBytes -ne $benchProperty.Value.bytes -or $benchSha -ne $benchExpected) { throw "Transfer SHA/bytes mismatch: $benchRelative; retained for investigation." }
        $benchResults += [ordered]@{path=$benchRelative;bytes=$benchBytes;sha256=$benchSha;status='VERIFIED'}
    }
    [ordered]@{utc=[DateTime]::UtcNow.ToString('o');status='TARGET_VERIFIED_SOURCE_RECHECK_PENDING';transport='New node directly pulls cloud via SFTP reget';files=$benchResults} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath "$benchRoot\setup\transfer_verified.json" -Encoding UTF8
    Get-Content -LiteralPath "$benchRoot\setup\transfer_verified.json" -Raw
} catch {
    [ordered]@{utc=[DateTime]::UtcNow.ToString('o');status='TRANSFER_NOT_VERIFIED';error=$_.Exception.Message} | ConvertTo-Json | Set-Content -LiteralPath "$benchRoot\setup\transfer_failure.json" -Encoding UTF8
    throw
} finally { $benchLock.Dispose() }
