"""Supplemental execution of independently reviewed unchanged source spans."""
import ast
import hashlib
import json
from pathlib import Path
from veronica_core.capability_reports import load_fixtures
from veronica_core.execution_sandbox import DockerSandbox

root = Path(__file__).parent
records = {r['case_id']: r for r in map(json.loads, (root/'results.jsonl').read_text(encoding='utf-8').splitlines())}
fixtures = {f['id']: f for f in load_fixtures()['cases']}
sandbox = DockerSandbox()
report = {'kind':'reviewed_extraction_supplement', 'foundation_qualified':False,
          'original_report_preserved':True, 'isolation':sandbox.verify(), 'cases':{}}
if report['isolation'].get('verified'):
    for case_id in ('CD-02', 'CD-03'):
        content = records[case_id]['message']['content']
        if case_id == 'CD-02':
            start = content.index('def page_count(total, size):')
            end = content.index('\n```', start)
        else:
            start = 0
            end = content.index('\n\n**Explanation:**')
        source = content[start:end]
        ast.parse(source)  # syntax inspection only; execution stays in Docker
        (root/f'{case_id}-reviewed-source.py').write_text(source, encoding='utf-8')
        outcome = sandbox.run_fixture(source, fixtures[case_id], 8)
        report['cases'][case_id] = {'start_offset':start, 'end_offset':end,
            'response_content_sha256':hashlib.sha256(content.encode()).hexdigest(),
            'source_unchanged':True, 'outcome':outcome}
else:
    report['status'] = 'isolation_unverified'
(root/'reviewed-extraction-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({k:{'passed':v['outcome']['ok'], 'vectors':len(v['outcome']['vectors'])} for k,v in report['cases'].items()}))
