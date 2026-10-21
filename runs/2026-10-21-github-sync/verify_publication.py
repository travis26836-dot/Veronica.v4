"""Test publishable changes over HEAD without unrelated dirty working files.

Run from the repository root with the project's Python environment. No network,
credentials or paid resources are used. Raw JUnit output remains local.
"""
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = Path(__file__).resolve().parent
CHANGED = [
    'config/runpod-t2-global.json', 'scripts/prepare_runpod_model.py',
    'scripts/runpod_core.py', 'scripts/runpod_windows_bridge.py',
    'scripts/start-veronica-universal.ps1', 'scripts/supervised_runpod.py',
    'src/veronica_core/universal_start.py', 'src/veronica_core/static/app.js',
    'tests/test_global_storage_launch.py',
]
SUITES = [
    'tests/test_global_storage_launch.py', 'tests/test_runpod_core.py',
    'tests/test_runpod_safety.py', 'tests/test_supervised_start.py',
    'tests/test_universal_start.py', 'tests/test_start_veronica.py',
]


def main():
    base = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    archive = subprocess.check_output([
        'git', 'archive', '--format=tar', base, 'src', 'tests', 'scripts', 'config',
        'docs', '.github', 'pyproject.toml', 'README.md', 'AGENTS.md',
    ], cwd=ROOT)
    with tempfile.TemporaryDirectory(prefix='clean-publication-', dir=EVIDENCE) as folder:
        clean = Path(folder)
        assert clean.resolve().is_relative_to(EVIDENCE.resolve())
        with tarfile.open(fileobj=io.BytesIO(archive)) as bundle:
            bundle.extractall(clean, filter='data')
        for relative in CHANGED:
            target = clean / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((ROOT / relative).read_bytes())
        environment = os.environ.copy()
        environment['PYTHONPATH'] = str(clean / 'src')
        for name in ('VERONICA_RUNPOD_WINDOWS_CLI', 'RUNPOD_API_KEY', 'VERONICA_UPSTREAM_API_KEY'):
            environment.pop(name, None)
        command = [sys.executable, '-m', 'pytest', *SUITES, '-q',
                   '--basetemp=' + str(clean / 'pytest-temp'),
                   '--junitxml=' + str(EVIDENCE / 'clean-tests.xml')]
        result = subprocess.run(command, cwd=clean, env=environment, timeout=300,
                                capture_output=True, text=True)
        (EVIDENCE / 'clean-pytest.log').write_text(result.stdout + result.stderr, encoding='utf-8')
        print((result.stdout + result.stderr)[-2500:])
        xml = ET.parse(EVIDENCE / 'clean-tests.xml')
        suites = list(xml.iter('testsuite'))
        counts = {name: sum(int(s.attrib.get(name, 0)) for s in suites)
                  for name in ('tests', 'failures', 'errors', 'skipped')}
        counts['passed'] = counts['tests'] - counts['failures'] - counts['errors'] - counts['skipped']
        (EVIDENCE / 'validation.json').write_text(json.dumps({
            'baseCommit': base, 'method': 'HEAD archive plus only the listed publication source changes',
            'changedFiles': CHANGED, 'suites': SUITES, 'exitCode': result.returncode,
            'counts': counts, 'paidResourceCreated': False,
        }, indent=2) + '\n', encoding='utf-8')
        return result.returncode


if __name__ == '__main__':
    raise SystemExit(main())
