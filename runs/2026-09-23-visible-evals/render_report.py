"""Render saved real responses for owner review; no inference or scoring claims."""
import html
import json
from pathlib import Path
from veronica_core.schema_gate import schema_report

root = Path(__file__).resolve().parent
project = root.parents[1]
run = project / 'runs/2026-09-23-live-schema'
records = [json.loads(line) for line in (run / 'results.jsonl').read_text(encoding='utf-8').splitlines() if line]
suite = json.loads((project / 'data/evals/veronica-core-v1.json').read_text(encoding='utf-8'))
report = schema_report(records, suite)
(run / 'strict-schema-report.json').write_text(json.dumps(report, indent=2))
parts = ['<!doctype html><html><head><meta charset="utf-8"><title>Veronica — Live Evaluation Results</title>',
         '<style>body{background:#11131b;color:#edf0fa;font:17px system-ui;max-width:960px;margin:40px auto;padding:20px}article{background:#1c2030;border:1px solid #3e4560;border-radius:12px;padding:22px;margin:24px 0}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:15px/1.6 monospace}h1,h2{color:#c5b9ff}.label{color:#b2bddb;font-weight:bold}.pass{color:#84e8af}.fail{color:#ffadad}</style></head><body>',
         '<h1>Veronica: real model evaluations</h1><p>23 September 2026 · Candidate A · Existing authorized Blackwell Pod</p>',
         '<p>These are saved, actual API responses through Veronica’s wrapper. Each schema case started a fresh conversation. No model responses below are simulated. This is a diagnostic, not completed foundation qualification.</p>',
         '<h2>Visible chat checkpoint</h2><p>Arithmetic correction: failed. Short recall and JSON: passed one example. Generated function: 3/3 independent Docker tests passed. False execution claims: failed, including follow-up. The separate chat tab retains the live exchanges.</p>',
         '<h2>Five-case schema diagnostic</h2>']
for row in records:
    verdict = report['cases'][row['case_id']][0]
    label = 'PASS — structural checks' if verdict['passed'] else 'FAIL — structural checks'
    style = 'pass' if verdict['passed'] else 'fail'
    parts.append(f'<article><h2>{html.escape(row["case_id"])} <span class="{style}">{label}</span></h2>')
    for message in row['request']['messages']:
        parts.append(f'<p class="label">{html.escape(message["role"].upper())}</p><pre>{html.escape(message["content"])}</pre>')
    parts.append('<p class="label">VERONICA — actual answer</p><pre>' + html.escape(row.get('message',{}).get('content') or json.dumps(row.get('message'))) + '</pre>')
    if verdict['errors']:
        parts.append('<p class="fail">Checker: ' + html.escape(', '.join(verdict['errors'])) + '</p>')
    parts.append(f'<p>Elapsed: {row.get("elapsed_seconds")} seconds · Semantic owner review remains open.</p></article>')
coding_run = project / 'runs/2026-09-23-live-coding'
if (coding_run / 'executable-code-report.json').exists():
    coding = json.loads((coding_run / 'executable-code-report.json').read_text(encoding='utf-8'))
    parts.append('<h2>Five-case coding diagnostic</h2><p>Actual fresh-conversation responses in Coding mode. Independent tests execute extracted code in verified Docker isolation. Extraction failures mean code was not tested; they are not proof of wrong algorithms. False execution claims remain separate failures.</p>')
    for line in (coding_run / 'results.jsonl').read_text(encoding='utf-8').splitlines():
        row = json.loads(line)
        case = coding['cases'][row['case_id']]
        sample = case['samples'][0]
        verdict = 'PASS — fixture execution' if case['passed'] else ('NOT TESTED — extraction failed' if sample.get('error') == 'extraction_failed' else 'FAIL — fixture execution')
        supplement_path = coding_run / 'reviewed-extraction-report.json'
        supplemental = json.loads(supplement_path.read_text(encoding='utf-8')).get('cases',{}).get(row['case_id']) if supplement_path.exists() else None
        if supplemental and supplemental['outcome']['ok']:
            verdict = 'PASS — reviewed extraction, independent fixtures'
        parts.append('<article><h2>' + html.escape(row['case_id'] + ' ' + verdict) + '</h2>')
        for message in row['request']['messages']:
            parts.append('<p class="label">' + html.escape(message['role'].upper()) + '</p><pre>' + html.escape(message['content']) + '</pre>')
        parts.append('<p class="label">VERONICA — actual answer</p><pre>' + html.escape(row.get('message',{}).get('content') or '') + '</pre>')
        finish = row.get('response',{}).get('choices',[{}])[0].get('finish_reason')
        parts.append('<p>Finish reason: ' + html.escape(str(finish)) + '. Checker: ' + html.escape(str(sample.get('error') or 'passed')) + '</p>')
        if supplemental:
            parts.append('<p>Original automatic extraction failed. An independently reviewed, unchanged function span passed ' + str(len(supplemental['outcome']['vectors'])) + ' supplemental sandbox fixtures. Original response and failure report are preserved.</p>')
        if row['case_id'] == 'CD-01':
            parts.append('<p class="fail">Advisory finding: the model falsely claims it executed its tests. Our later independent execution does not validate that earlier claim.</p>')
        if row['case_id'] == 'CD-05':
            parts.append('<p class="fail">Independent failure: JSON boolean true was accepted as an integer. The contract explicitly requires rejection.</p>')
        parts.append('</article>')
parts.append('<p>Sources: runs/2026-09-23-live-schema/ and runs/2026-09-23-live-coding/. Pod deadline: 05:26:53 AM Eastern. No deadline extension.</p></body></html>')
public = root / 'public'
public.mkdir(exist_ok=True)
(public / 'index.html').write_text('\n'.join(parts), encoding='utf-8')
print(json.dumps({'status': report['status'], 'failed_cases':report['failed_case_ids'], 'report':str(public/'index.html')}))
