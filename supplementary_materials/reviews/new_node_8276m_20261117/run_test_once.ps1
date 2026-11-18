$ErrorActionPreference = 'Stop'
$benchRoot = 'C:\NationalModelBench\ops_open2050_t32_20261118'
$benchSource = "$benchRoot\runsource\t32_factor5_v1"
$benchOutput = "$benchRoot\runs\t32_factor5_v1"
$benchPython = 'C:\NationalModelBench\envs\gurobi1302_py31020\python.exe'
$benchLicense = 'C:\Users\zz2\gurobi.lic'
$benchReceipt = "$benchSource\controller_started.json"
if (Test-Path -LiteralPath $benchReceipt) { throw 'This one-time controller has already started; inspect old task, do not repeat.' }
if (Test-Path -LiteralPath $benchOutput) { throw 'Output directory already exists; refusing to overwrite.' }
if (-not (Test-Path -LiteralPath $benchLicense)) { throw 'License path missing; no test started.' }
$benchAuth = Get-Content -LiteralPath "$benchRoot\setup\execution_authorization.json" -Raw | ConvertFrom-Json
if ($benchAuth.status -ne 'AUTHORIZED' -or 'run' -notin $benchAuth.allowed_modes) { throw 'Author has not released this run.' }
$benchManifest = Get-Content -LiteralPath "$benchSource\source_manifest.json" -Raw | ConvertFrom-Json
foreach ($benchFile in $benchManifest.files) {
    $benchPath = Join-Path $benchSource $benchFile.path
    if ((Get-FileHash -LiteralPath $benchPath -Algorithm SHA256).Hash.ToLower() -ne $benchFile.sha256) { throw "Code SHA mismatch: $($benchFile.path)" }
}
$env:GRB_LICENSE_FILE = $benchLicense
$env:OPENBLAS_NUM_THREADS = '1'
$env:MKL_NUM_THREADS = '1'
$env:OMP_NUM_THREADS = '1'
$env:PYTHONDONTWRITEBYTECODE = '1'
$benchArguments = '"'+$benchSource+'\benchmark_mps.py" run --root "'+$benchRoot+'" --output "'+$benchOutput+'"'
$benchChild = Start-Process -FilePath $benchPython -ArgumentList $benchArguments -WorkingDirectory $benchRoot -WindowStyle Hidden -RedirectStandardOutput "$benchSource\console.stdout.log" -RedirectStandardError "$benchSource\console.stderr.log" -PassThru
[ordered]@{utc=[DateTime]::UtcNow.ToString('o');controller_pid=$PID;solver_pid=$benchChild.Id;output=$benchOutput;license_path=$benchLicense;max_new_license_environments=1;threads=32;barrier_iterations=5;source_commit=$benchManifest.code_commit} | ConvertTo-Json | Set-Content -LiteralPath $benchReceipt -Encoding UTF8
$benchChild.WaitForExit()
$benchChild.Refresh()
[ordered]@{utc=[DateTime]::UtcNow.ToString('o');solver_pid=$benchChild.Id;exit_code=$benchChild.ExitCode;terminal_exists=(Test-Path -LiteralPath "$benchOutput\terminal.json");output=$benchOutput} | ConvertTo-Json | Set-Content -LiteralPath "$benchSource\controller_finished.json" -Encoding UTF8
if ($benchChild.ExitCode -ne 0) { exit 1 }
