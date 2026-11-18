$ErrorActionPreference = 'Stop'
$benchRoot = 'C:\NationalModelBench\ops_open2050_t32_20261118'
$benchRuntime = 'C:\NationalModelBench\miniforge_26.9.4-2'
$benchEnv = 'C:\NationalModelBench\envs\gurobi1302_py31020'
New-Item -ItemType Directory -Path "$benchRoot\setup" -Force | Out-Null
function Invoke-BenchProcess($benchExecutable, $benchArguments, $benchOutputName) {
    $benchStdout = "$benchRoot\setup\$benchOutputName"
    $benchStderr = "$benchStdout.stderr"
    foreach ($benchLog in @($benchStdout,$benchStderr)) {
        if (Test-Path -LiteralPath $benchLog) { Copy-Item -LiteralPath $benchLog -Destination ($benchLog+'.'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfff')+'.previous') }
    }
    $benchProcess = Start-Process -FilePath $benchExecutable -ArgumentList $benchArguments -WorkingDirectory $benchRoot -WindowStyle Hidden -RedirectStandardOutput $benchStdout -RedirectStandardError $benchStderr -Wait -PassThru
    if ($benchProcess.ExitCode -ne 0) { throw "$benchOutputName exited $($benchProcess.ExitCode); stdout/stderr retained" }
}
$benchLock = [System.IO.File]::Open("$benchRoot\setup\bootstrap.lock",[System.IO.FileMode]::OpenOrCreate,[System.IO.FileAccess]::ReadWrite,[System.IO.FileShare]::None)
try {
    $benchInstaller = "$benchRoot\setup\Miniforge3-26.9.4-2-Windows-x86_64.exe"
    $benchUrl = 'https://github.com/conda-forge/miniforge/releases/download/26.9.4-2/Miniforge3-Windows-x86_64.exe'
    $benchExpected = '9d83983669bc5d3b5dd4c631454bf953c3caf4ac78b9c9ada9971e5b021d83c3'
    if (-not (Test-Path -LiteralPath $benchInstaller)) {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $benchUrl -OutFile $benchInstaller -UseBasicParsing
    }
    $benchActual = (Get-FileHash -LiteralPath $benchInstaller -Algorithm SHA256).Hash.ToLower()
    if ($benchActual -ne $benchExpected) { throw 'Installer checksum mismatch; retained file for investigation, no install.' }
    [ordered]@{utc=[DateTime]::UtcNow.ToString('o');url=$benchUrl;sha256=$benchActual;bytes=(Get-Item -LiteralPath $benchInstaller).Length} | ConvertTo-Json | Set-Content -LiteralPath "$benchRoot\setup\installer_verified.json" -Encoding UTF8
    if (-not (Test-Path -LiteralPath "$benchRuntime\Scripts\conda.exe")) {
        if (Test-Path -LiteralPath $benchRuntime) { throw 'Partial runtime directory exists; inspect before retrying.' }
        $benchInstallProcess = Start-Process -FilePath $benchInstaller -ArgumentList '/InstallationType=JustMe','/RegisterPython=0','/AddToPath=0','/S',"/D=$benchRuntime" -WindowStyle Hidden -Wait -PassThru
        if ($benchInstallProcess.ExitCode -ne 0) { throw "Installer exited $($benchInstallProcess.ExitCode)" }
    }
    $benchCondaAction = 'create'
    if (Test-Path -LiteralPath "$benchEnv\conda-meta\history") { $benchCondaAction = 'install' }
    Invoke-BenchProcess "$benchRuntime\Scripts\conda.exe" "$benchCondaAction --yes --prefix $benchEnv --override-channels --channel conda-forge --no-shortcuts python=3.10.20 pip numpy=1.26.4 psutil=7.0.0" 'conda_create.log'
    Invoke-BenchProcess "$benchEnv\python.exe" '-m pip install --disable-pip-version-check gurobipy==13.0.2' 'pip_install.log'
    Invoke-BenchProcess "$benchEnv\python.exe" '-m pip install --disable-pip-version-check scipy==1.15.3' 'scipy_install.log'
    Invoke-BenchProcess "$benchEnv\python.exe" '-m pip check' 'pip_check.log'
    Invoke-BenchProcess "$benchEnv\python.exe" '-m pip freeze' 'pip_freeze.txt'
    Invoke-BenchProcess "$benchRuntime\Scripts\conda.exe" "list --prefix $benchEnv --explicit" 'conda_explicit.txt'
    Invoke-BenchProcess "$benchEnv\python.exe" '-c "import json,sys,gurobipy,numpy,scipy,psutil; print(json.dumps(dict(python=sys.version,gurobi=gurobipy.gurobi.version(),numpy=numpy.__version__,scipy=scipy.__version__,psutil=psutil.__version__)))"' 'versions.json'
    [ordered]@{utc=[DateTime]::UtcNow.ToString('o');status='RUNTIME_READY_LICENSE_NOT_TESTED';runtime=$benchRuntime;environment=$benchEnv;installer_sha256=$benchActual} | ConvertTo-Json | Set-Content -LiteralPath "$benchRoot\setup\bootstrap_complete.json" -Encoding UTF8
    Get-Content -LiteralPath "$benchRoot\setup\bootstrap_complete.json" -Raw
} catch {
    [ordered]@{utc=[DateTime]::UtcNow.ToString('o');status='SETUP_FAILED';error=$_.Exception.Message} | ConvertTo-Json | Set-Content -LiteralPath ("$benchRoot\setup\bootstrap_failure_"+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfff')+'.json') -Encoding UTF8
    throw
} finally { $benchLock.Dispose() }
