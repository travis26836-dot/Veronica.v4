"""Offline Global Volume attachment and single-resource safety regressions."""
import importlib.util
import hashlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


bridge = load('runpod_windows_bridge')
core = load('runpod_core')


def test_global_bridge_requires_verified_cache_artifact(monkeypatch, tmp_path):
    monkeypatch.setattr(bridge, 'ROOT', tmp_path)
    monkeypatch.setenv('WSLENV', '')
    monkeypatch.setenv('VERONICA_RUNPOD_WINDOWS_CLI', '')
    path = tmp_path / '.cache/runpod/runpodctl.exe'
    profile = {'pod': {'storageType': 'global', 'globalVolumeId': 'volume',
                      'networkVolumeId': 'volume', 'windowsCliPath': str(path.relative_to(tmp_path)),
                      'windowsCliSha256': hashlib.sha256(b'verified-binary').hexdigest()}}
    with pytest.raises(ValueError, match='cache artifact is missing'):
        bridge.configure(profile)
    path.parent.mkdir(parents=True)
    path.write_bytes(b'tampered-binary')
    with pytest.raises(ValueError, match='checksum changed'):
        bridge.configure(profile)
    assert not bridge.os.environ['VERONICA_RUNPOD_WINDOWS_CLI']
    path.write_bytes(b'verified-binary')
    bridge.configure(profile)
    assert bridge.os.environ['VERONICA_RUNPOD_WINDOWS_CLI'] == profile['pod']['windowsCliPath']
    assert 'VERONICA_RUNPOD_WINDOWS_CLI' in bridge.os.environ['WSLENV'].split(':')


def test_global_bridge_rejects_artifacts_outside_cache(monkeypatch, tmp_path):
    monkeypatch.setattr(bridge, 'ROOT', tmp_path)
    path = tmp_path / 'runs/runpodctl.exe'
    path.parent.mkdir()
    path.write_bytes(b'verified-binary')
    profile = {'pod': {'storageType': 'global', 'globalVolumeId': 'volume',
                      'networkVolumeId': 'volume', 'windowsCliPath': 'runs/runpodctl.exe',
                      'windowsCliSha256': hashlib.sha256(path.read_bytes()).hexdigest()}}
    with pytest.raises(ValueError, match='cache artifact is missing'):
        bridge.configure(profile)


def create_args():
    return ['pod', 'create', '--name', 'veronica-core-offline', '--image', 'image@sha256:' + 'a'*64,
            '--gpu-id', 'NVIDIA A100-SXM4-80GB', '--gpu-count', '1', '--cloud-type', 'SECURE',
            '--data-center-ids', 'US-KS-2', '--global-volume-id', 'existing-global-volume',
            '--container-disk-in-gb', '30', '--volume-mount-path', '/workspace', '--ports', '22/tcp',
            '--min-cuda-version', '12.8', '--ssh', '--env', '{"PUBLIC_KEY":"offline-public-key"}']


def test_global_create_attaches_existing_volume_without_regional_storage():
    body = bridge.global_create_payload(create_args())
    assert body['mounts'] == {'global': [{'volumeId': 'existing-global-volume', 'path': '/workspace'}]}
    assert body['gpu']['count'] == 1
    assert body['ports'] == ['22/tcp'] and body['startSsh'] and not body['startJupyter']


@pytest.mark.parametrize('flag,value', [('--gpu-count', '2'), ('--ports', '8000/http'),
                                      ('--cloud-type', 'COMMUNITY'), ('--global-volume-id', '../other')])
def test_global_create_rejects_scope_expansion(flag, value):
    args = create_args()
    args[args.index(flag)+1] = value
    with pytest.raises(ValueError):
        bridge.global_create_payload(args)


def test_http_transport_failure_is_uncertain_and_never_retried(monkeypatch):
    calls = []
    def run(*args, **kwargs):
        calls.append((args, kwargs))
        return SimpleNamespace(returncode=28, stdout=b'\n000')
    monkeypatch.setattr(bridge.subprocess, 'run', run)
    with pytest.raises(TimeoutError):
        bridge.request('https://api.runpod.io/v2/pods', {}, 'offline-secret')
    assert len(calls) == 1
    assert 'offline-secret' not in str(calls[0][0])
    assert b'offline-secret' in calls[0][1]['input']


@pytest.mark.parametrize('status', [401, 403])
def test_auth_probe_preserves_expected_http_error_contract(monkeypatch, status):
    monkeypatch.setattr(bridge.subprocess, 'run', lambda *a, **k: SimpleNamespace(returncode=0, stdout=f'private-body\n{status}'.encode()))
    with pytest.raises(HTTPError) as failure:
        bridge.request('http://127.0.0.1:18000/v1/models')
    assert failure.value.code == status
    assert isinstance(failure.value, bridge.RejectedRequest)
    assert 'private-body' not in str(failure.value)


def test_provider_smoke_accepts_expected_unauthenticated_rejection_through_bridge(monkeypatch, tmp_path):
    calls = []
    def run(*args, **kwargs):
        config = kwargs['input'].decode()
        calls.append(config)
        if 'Authorization: Bearer' not in config:
            return SimpleNamespace(returncode=0, stdout=b'{}\n401')
        if '/models' in config:
            return SimpleNamespace(returncode=0, stdout=b'{"data":[{"id":"Veronica"}]}\n200')
        response = {'choices': [{'message': {'content': 'Raine remembers copper lantern.'}}]}
        return SimpleNamespace(returncode=0, stdout=json.dumps(response).encode()+b'\n200')
    monkeypatch.setattr(bridge.subprocess, 'run', run)
    monkeypatch.setattr(core, 'fetch', bridge.request)
    monkeypatch.setattr(core, 'evidence_directory', lambda p: p)
    monkeypatch.setenv('VERONICA_UPSTREAM_API_KEY', 'offline-test-key')
    core.verify({'publicAlias': 'Veronica'}, 'http://127.0.0.1:18000/v1', tmp_path)
    result = json.loads((tmp_path/'provider-smoke.json').read_text())
    assert result['unauthenticatedModelsStatus'] == 401 and result['basicSmokePassed']
    assert len(result['tests']) == 5 and len(calls) == 7


def test_server_http_error_is_not_a_definitive_creation_rejection(monkeypatch):
    monkeypatch.setattr(bridge.subprocess, 'run', lambda *a, **k: SimpleNamespace(returncode=0, stdout=b'{}\n503'))
    with pytest.raises(HTTPError) as failure:
        bridge.request('https://api.runpod.io/v2/pods', {})
    assert not isinstance(failure.value, bridge.RejectedRequest)


def test_ssh_keeps_private_key_and_host_verification_in_wsl(monkeypatch):
    monkeypatch.setattr(bridge, 'windows_path', lambda path: 'C:/project/scripts/runpod_windows_bridge.py')
    original = ['ssh', '-i', '/home/controller/.ssh/private', '-o',
                'StrictHostKeyChecking=accept-new', 'root@192.0.2.1']
    command = bridge.ssh_command(original)
    assert command[0] == 'ssh'
    assert command[3:] == original[1:]
    assert '--ssh-proxy' in command[2] and '%h %p' in command[2]
    assert '/home/controller/.ssh/private' not in command[2]


def test_loading_progress_exposes_hash_counts_without_raw_log_secrets(monkeypatch, tmp_path):
    monkeypatch.setitem(sys.modules, 'runpod_core', core)
    controller = load('supervised_runpod')
    monkeypatch.setattr(controller, 'remote_dir', lambda run: '/tmp/run')
    monkeypatch.setattr(controller, 'ssh', lambda *a, **k: b'secret-token\nVERIFIED model-00001-of-00013.safetensors\nVERIFIED model-00002-of-00013.safetensors\n')
    message = controller.loading_progress(tmp_path)
    assert '2/13' in message and 'secret-token' not in message


def test_loading_progress_reports_actual_runtime_eta(monkeypatch, tmp_path):
    monkeypatch.setitem(sys.modules, 'runpod_core', core)
    controller = load('supervised_runpod')
    monkeypatch.setattr(controller, 'remote_dir', lambda run: '/tmp/run')
    monkeypatch.setattr(controller, 'ssh', lambda *a, **k: b'Loading safetensors checkpoint shards: 46% Completed | 6/13 [02:20<02:47, 23.90s/it]\n')
    message = controller.loading_progress(tmp_path)
    assert '6/13' in message and '46%' in message and 'ETA 02:47' in message


def test_tunnel_anchor_cannot_open_after_authorized_deadline(monkeypatch, tmp_path):
    monkeypatch.setitem(sys.modules, 'runpod_core', core)
    controller = load('supervised_runpod')
    monkeypatch.setattr(controller, 'state_at', lambda run: {'deadlineUtc': (datetime.now(timezone.utc)-timedelta(seconds=1)).isoformat()})
    monkeypatch.setattr(controller, 'connection', lambda run: pytest.fail('Expired tunnel must not connect'))
    with pytest.raises(RuntimeError, match='authorized tunnel window'):
        controller.tunnel(tmp_path, hold=True)


def test_global_tunnel_uses_owned_controller_anchor(monkeypatch, tmp_path):
    monkeypatch.setitem(sys.modules, 'runpod_core', core)
    monkeypatch.setitem(sys.modules, 'runpod_windows_bridge', bridge)
    controller = load('supervised_runpod')
    monkeypatch.setattr(controller, 'state_at', lambda run: {'deadlineUtc': (datetime.now(timezone.utc)+timedelta(minutes=1)).isoformat()})
    monkeypatch.setenv('VERONICA_RUNPOD_WINDOWS_CLI', 'test')
    calls = []
    monkeypatch.setattr(bridge, 'launch_tunnel_anchor', calls.append)
    controller.tunnel(tmp_path)
    assert calls == [tmp_path]


def global_inventory(profile, pods=()):
    def cli(*args):
        if args[:2] == ('global-volume', 'get'):
            return json.dumps({'id': profile['pod']['globalVolumeId']})
        if args[:2] == ('gpu', 'list'):
            return json.dumps([{'gpuId': profile['pod']['gpuTypeId'], 'securePricePerHr': 1.79,
                               'dataCenterAvailability': [{'dataCenterId': 'US-KS-2', 'stockStatus': 'Low'}]}])
        if args[:2] == ('pod', 'list'):
            return json.dumps(list(pods))
        if args[:2] == ('ssh', 'list-keys'):
            return '{"keys":["offline-public-key"]}'
        if args == ('version',):
            return 'offline-test'
        if args == ('pod', 'create', '--help'):
            return 'no platform timer'
        raise AssertionError(f'Unexpected/mutating call: {args}')
    return cli


def test_global_preflight_can_use_another_data_center_and_preserves_price_gate(monkeypatch):
    profile = json.loads((ROOT / 'config/runpod-t2-global.json').read_text())
    monkeypatch.setattr(core, 'cli', global_inventory(profile))
    result = core.preflight(profile, 1.79, 60, supervised=True)
    assert result['safeToCreate'] and result['dataCenterId'] == 'US-KS-2'
    assert not core.preflight(profile, 1.75, 60, supervised=True)['safeToCreate']
    assert not core.preflight(profile, 1.79, 60, supervised=False)['safeToCreate']


def test_global_preflight_blocks_second_gpu_during_migration(monkeypatch):
    profile = json.loads((ROOT / 'config/runpod-t2-global.json').read_text())
    monkeypatch.setattr(core, 'cli', global_inventory(profile, [{'name': 'veronica-volume-migration'}]))
    assert not core.preflight(profile, 1.79, 60, supervised=True)['safeToCreate']


def test_global_next_start_uses_reviewed_eager_network_loading():
    bootstrap = load('prepare_runpod_model')
    profile = json.loads((ROOT/'config/runpod-t2-global.json').read_text())
    arguments = bootstrap.validated_server_arguments(profile['runtime'])
    assert arguments[arguments.index('--safetensors-load-strategy')+1] == 'eager'
    assert profile['model']['revision'] == 'e2f73ec7e99ee316beb8069ca90e4c3cbef8aa0f'


@pytest.mark.parametrize('arguments', [
    ['--safetensors-load-strategy'],
    ['--safetensors-load-strategy','unknown'],
    ['--safetensors-load-strategy','eager','--safetensors-load-strategy','lazy'],
])
def test_load_strategy_rejects_malformed_or_ambiguous_configuration(arguments):
    bootstrap = load('prepare_runpod_model')
    with pytest.raises(ValueError):
        bootstrap.validated_server_arguments({'serverArguments':arguments})
