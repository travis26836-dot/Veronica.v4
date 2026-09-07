# Current user startup request

User: "If the model hasn't responded yet, we need to fix it"
Duration: 60 minutes, carried from the earlier "One hour is fine" for this session.

This is a recovery start after `runs/2026-09-04T065235Z-start-veronica` failed to install the frozen T2 runtime (vLLM 0.17.0 + Transformers 5.8.0 are unsatisfiable). Profile is the proven default `config/runpod-core.json` (vLLM 0.11.0 / Transformers 4.57.1, Candidate A) so the model can actually answer. This is not a T2 comparison and does not lift the T2 runtime hold.

Authorization for this one run: 60 minutes including startup, one A100 80 GB, maximum $1.75/hour, supervised shutdown. Persistent storage retained. No replacement or extension is authorized after this run.
