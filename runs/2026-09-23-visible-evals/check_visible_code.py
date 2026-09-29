"""Run only the visibly generated function in the established Docker sandbox."""
import json
from pathlib import Path
from veronica_core.capability_reports import load_fixtures
from veronica_core.execution_sandbox import DockerSandbox

root = Path(__file__).parent
raw = (root / 'coding-response.txt').read_text(encoding='utf-8')
# Preserve the raw answer. Extract the unchanged function preceding its tests;
# the model's asserted expected outputs and execution claims are not graders.
source = raw.split('\n# Tests\n', 1)[0]
fixture = next(c for c in load_fixtures()['cases'] if c['id'] == 'CD-01')
sandbox = DockerSandbox()
isolation = sandbox.verify()
result = {'source': 'visible browser tab 3', 'fixture': 'CD-01',
          'isolation': isolation, 'foundation_qualified': False}
if isolation.get('verified'):
    result['outcome'] = sandbox.run_fixture(source, fixture, 8)
else:
    result['status'] = 'isolation_unverified'
(root / 'coding-execution.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result, indent=2))
