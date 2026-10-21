"""RunPod transport for this Windows controller's working network.

Credentials stay in the existing WSL store and process environment/stdin.
Creation is single-shot; only the checked supervised controller calls it.
"""
from __future__ import annotations

import hashlib
import base64
import json
import os
from pathlib import Path
import re
import shlex
import socket
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from urllib.error import HTTPError
import tomllib

ROOT = Path(__file__).resolve().parents[1]


class RejectedRequest(HTTPError):
    """An explicit HTTP client rejection, rather than an uncertain transport."""


def configure(profile):
    if profile['pod'].get('storageType') != 'global':
        return
    pod = profile['pod']
    if pod.get('globalVolumeId') != pod.get('networkVolumeId'):
        raise ValueError('Legacy approval volume ID must identify the same Global Volume')
    path = (ROOT / pod['windowsCliPath']).resolve()
    if not path.is_relative_to(ROOT / '.cache/runpod') or not path.is_file():
        raise ValueError('Verified Windows CLI cache artifact is missing; see docs/goals/GLOBAL-STORAGE-LIVE-20261021.md')
    if hashlib.sha256(path.read_bytes()).hexdigest() != pod['windowsCliSha256']:
        raise ValueError('Windows CLI checksum changed')
    os.environ['VERONICA_RUNPOD_WINDOWS_CLI'] = pod['windowsCliPath']
    names = os.environ.get('WSLENV', '').split(':')
    if 'VERONICA_RUNPOD_WINDOWS_CLI' not in names:
        os.environ['WSLENV'] = ':'.join(filter(None, [*names, 'VERONICA_RUNPOD_WINDOWS_CLI']))


def credential():
    if os.name == 'nt':
        raise RuntimeError('Run the bridge in WSL; never copy credentials into the project')
    value = tomllib.loads((Path.home() / '.runpod/config.toml').read_text())['apikey']
    if not isinstance(value, str) or not value or any(c in value for c in '\r\n\0'):
        raise ValueError('Invalid stored RunPod credential')
    return value


def request(url, payload=None, key=None, method=None):
    # curl config on stdin keeps credentials out of command arguments and files.
    options = {'url': url, 'request': method or ('POST' if payload is not None else 'GET')}
    lines = [f'{k} = {json.dumps(v)}' for k, v in options.items()]
    lines.append('header = "Content-Type: application/json"')
    if key:
        lines.append('header = ' + json.dumps('Authorization: Bearer ' + key))
    if payload is not None:
        lines.append('data = ' + json.dumps(json.dumps(payload)))
    result = subprocess.run(
        ['/mnt/c/Windows/System32/curl.exe', '--silent', '--show-error', '--location',
         '--max-time', '60', '--write-out', '\n%{http_code}', '--config', '-'],
        input=('\n'.join(lines) + '\n').encode(), capture_output=True, timeout=65,
    )
    body, _, status = result.stdout.rpartition(b'\n')
    code = int(status) if status.isdigit() else 0
    if result.returncode or not code:
        raise TimeoutError(f'RunPod/network transport failed ({result.returncode}); no creation retry')
    if not 200 <= code < 300:
        error = RejectedRequest if 400 <= code < 500 and code not in (408, 429) else HTTPError
        # Preserve urllib's HTTP contract: verification intentionally expects
        # 401/403 without a key. Creation still distinguishes a definite 4xx
        # rejection from an uncertain transport/server response.
        raise error(url, code, 'HTTP request rejected; response body omitted', None, None)
    return body


def global_create_payload(args):
    values = {}
    i = 2
    while i < len(args):
        flag = args[i]
        if flag == '--ssh':
            values[flag] = True
            i += 1
        else:
            if not flag.startswith('--') or i + 1 >= len(args) or flag in values:
                raise ValueError('Malformed or duplicate create argument')
            values[flag] = args[i + 1]
            i += 2
    allowed = {'--name', '--image', '--gpu-id', '--gpu-count', '--cloud-type',
               '--data-center-ids', '--global-volume-id', '--container-disk-in-gb',
               '--volume-mount-path', '--ports', '--min-cuda-version', '--ssh', '--env'}
    if set(values) - allowed or values.get('--gpu-count') != '1':
        raise ValueError('Only a single explicitly configured GPU is supported')
    if values.get('--ports') != '22/tcp' or values.get('--cloud-type') != 'SECURE':
        raise ValueError('Global launch requires Secure Cloud and SSH-only ingress')
    volume = values['--global-volume-id']
    if not re.fullmatch(r'[A-Za-z0-9_-]+', volume):
        raise ValueError('Invalid Global Volume identifier')
    return {
        'name': values['--name'], 'image': values['--image'],
        'gpu': {'id': values['--gpu-id'], 'count': 1, 'minCudaVersion': values['--min-cuda-version']},
        'cloud': 'SECURE', 'disk': int(values['--container-disk-in-gb']),
        'dataCenterIds': values['--data-center-ids'].split(','),
        'mounts': {'global': [{'volumeId': volume, 'path': values['--volume-mount-path']}]},
        'ports': ['22/tcp'], 'startSsh': True, 'startJupyter': False,
        'env': json.loads(values['--env']),
    }


def cli(args):
    args = list(args)
    if args[:2] == ['global-volume', 'get']:
        if len(args) != 3 or not re.fullmatch(r'[A-Za-z0-9_-]+', args[2]):
            raise ValueError('Invalid Global Volume read')
        return request('https://api.runpod.io/v2/global-volumes/' + args[2], key=credential()).decode()
    if args[:2] == ['pod', 'create'] and '--global-volume-id' in args:
        return request('https://api.runpod.io/v2/pods', global_create_payload(args), credential()).decode()
    executable = ROOT / os.environ['VERONICA_RUNPOD_WINDOWS_CLI']
    env = os.environ.copy()
    env['RUNPOD_API_KEY'] = credential()
    env['WSLENV'] = ':'.join(filter(None, [env.get('WSLENV'), 'RUNPOD_API_KEY']))
    result = subprocess.run([str(executable), *args], env=env, capture_output=True, text=True, timeout=60)
    if result.returncode:
        raise RuntimeError(f'Windows RunPod CLI failed with exit {result.returncode}; inspect the service, never retry creation')
    return result.stdout


def windows_path(path):
    return subprocess.check_output(['wslpath', '-w', str(path)], text=True).strip()


def ssh_command(args):
    # Keep key handling and host verification in WSL OpenSSH. Only its encrypted
    # socket crosses Windows networking; private keys never leave the WSL store.
    python = ROOT / '.venv/Scripts/python.exe'
    proxy = shlex.join([str(python), windows_path(__file__), '--ssh-proxy']) + ' %h %p'
    return [args[0], '-o', 'ProxyCommand=' + proxy, *args[1:]]


def ssh_proxy(host, port):
    """Binary stdin/stdout socket relay used exclusively by OpenSSH ProxyCommand."""
    with socket.create_connection((host, int(port)), timeout=15) as connection:
        connection.settimeout(None)
        def upload():
            try:
                while data := sys.stdin.buffer.read1(65536):
                    connection.sendall(data)
                connection.shutdown(socket.SHUT_WR)
            except OSError:
                pass
        threading.Thread(target=upload, daemon=True).start()
        while data := connection.recv(65536):
            sys.stdout.buffer.write(data)
            sys.stdout.buffer.flush()


def launch_tunnel_anchor(run):
    """Keep the interop relay alive in a hidden, independently owned WSL host."""
    arguments = ['-d', os.environ['WSL_DISTRO_NAME'], '-e', 'python3', '-B',
                 str(ROOT / 'scripts/supervised_runpod.py'), 'tunnel-anchor', '--run-dir', str(run)]
    def literal(value):
        return "'" + str(value).replace("'", "''") + "'"
    quoted = [literal('"' + value + '"' if any(c.isspace() for c in value) else value) for value in arguments]
    output = windows_path(run / 'tunnel-anchor.stdout.log')
    error = windows_path(run / 'tunnel-anchor.stderr.log')
    pid_path = run / 'tunnel-anchor.pid'
    script = ("$ErrorActionPreference='Stop'; $process=Start-Process -FilePath wsl.exe -WindowStyle Hidden "
              '-ArgumentList @(' + ','.join(quoted) + ') -PassThru -RedirectStandardOutput ' + literal(output)
              + ' -RedirectStandardError ' + literal(error) + '; $process.Id | Set-Content -LiteralPath '
              + literal(windows_path(pid_path)))
    requested = datetime.now(timezone.utc)
    subprocess.Popen(['/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe',
                      '-NoProfile', '-EncodedCommand', base64.b64encode(script.encode('utf-16le')).decode()],
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(60):
        try:
            record = json.loads((run / 'tunnel.json').read_text())
            if record.get('heldOpen') and datetime.fromisoformat(record['atUtc']) >= requested:
                pid = int(pid_path.read_text(encoding='utf-8-sig').strip())
                (run / 'tunnel-anchor-windows.json').write_text(json.dumps({'pid': pid,
                    'requestedAtUtc': requested.isoformat(), 'runId': run.name}))
                return
        except (OSError, ValueError):
            pass
        time.sleep(0.5)
    raise RuntimeError('Tunnel anchor did not acknowledge readiness; inspect its owned logs')



if __name__ == '__main__':
    if len(sys.argv) == 4 and sys.argv[1] == '--ssh-proxy':
        ssh_proxy(sys.argv[2], sys.argv[3])
    else:
        print(cli(sys.argv[1:]), end='')
