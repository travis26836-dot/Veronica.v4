# Startup launcher test capture

**Status:** passed after policy-aligned assertion update

## Command

```powershell
uv run pytest tests/test_start_veronica.py -q
```

## Result

- Exit status: `0`
- Tests: 30 passed
- No Pod, credentials, resource creation, or live model request was used.

The complete captured output is in `combined.txt`; `exit.txt` contains the command exit status.

## Initial failure and resolution

The first captured run had exit status `1`: 28 passed and two failures. Both
were stale expectations in `tests/test_start_veronica.py`:

1. `test_plan_only_works_without_wsl_or_approval_and_makes_no_changes` expects `maxHourlyUsd == 2.09`; the launcher now reports `1.75`.
2. `test_explicit_options_override_defaults_without_raising_saved_ceiling` expects `maximumHourlyUsd == 2.09`; the launcher now reports `1.75`.

The assertion update to `1.75` was made after the accepted launch-policy
correction. The final rerun above is the passing result.

## Limitation

A prior run completed with dot-only output but did not durably capture its exit status, so it is excluded from the final result. A first PowerShell background wrapper was also discarded because it did not record an exit file after the child finished. The final `cmd.exe` capture above is the reproducible evidence.

## Next safe action

The startup-test capture gate is complete. The next safe action is to integrate
the reviewed Core packet from its clean branch, then proceed to the separately
authorized live four-model qualification.
