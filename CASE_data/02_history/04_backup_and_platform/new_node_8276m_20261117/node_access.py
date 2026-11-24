"""Explicit SSH helpers for the authorized 8276M test node; no credential reads."""
import base64
import subprocess
from pathlib import Path

NODE_SSH = [
    'ssh', '-p', '2222', '-i', str(Path.home()/'.ssh/id_ed25519_national_8276m'),
    '-o', 'IdentitiesOnly=yes', '-o', 'BatchMode=yes',
    '-o', 'StrictHostKeyChecking=yes', '-o', 'ConnectTimeout=15',
    '-o', 'ConnectionAttempts=1', '-o', 'ServerAliveInterval=15',
    '-o', 'ServerAliveCountMax=3', 'zz2@127.0.0.1',
]

def powershell(script, timeout=90):
    prefix = '[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding\n'
    encoded = base64.b64encode((prefix+script).encode('utf-16le')).decode()
    result = subprocess.run(NODE_SSH + ['powershell.exe -NoProfile -NonInteractive -EncodedCommand '+encoded],
                            capture_output=True, timeout=timeout)
    stdout = result.stdout.decode('utf-8', errors='replace').strip()
    stderr = result.stderr.decode('utf-8', errors='replace').strip()
    if result.returncode:
        raise RuntimeError(f'Node command exit={result.returncode}: {stdout}\n{stderr[:4000]}')
    return stdout

def cloud_python(code, timeout=120):
    encoded = base64.b64encode(code.encode('utf-8')).decode()
    command = 'printf %s ' + encoded + ' | base64 -d | python3 -'
    script = "& ssh.exe -F C:/Users/zz2/.ssh/config_paracloud_8276m paracloud-8276m '" + command + "'\nexit $LASTEXITCODE"
    return powershell(script,timeout)
