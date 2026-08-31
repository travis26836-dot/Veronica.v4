# Candidate provenance checkpoint — 2026-08-30

## Outcome

The two Veronica candidate repositories and their matching official controls now have immutable Hugging Face commit revisions recorded. This is a provenance discovery checkpoint only; it does not qualify a model, validate a copied artifact, start inference, or authorize paid GPU use.

## Immutable revisions and remote manifests

| Role | Repository | Immutable revision | Declared license | LFS artifacts | LFS bytes |
| --- | --- | --- | --- | ---: | ---: |
| Candidate A | `huihui-ai/Huihui-Qwen3-30B-A3B-Instruct-2507-abliterated` | `e2f73ec7e99ee316beb8069ca90e4c3cbef8aa0f` | Apache-2.0 | 14 | 61,078,000,382 |
| Candidate A control | `Qwen/Qwen3-30B-A3B-Instruct-2507` | `0d7cf23991f47feeb3a57ecb4c9cee8ea4a17bfe` | Apache-2.0 | 17 | 61,077,998,310 |
| Candidate B | `huihui-ai/Huihui-Qwen3.8-27B-abliterated` | `739e3c5b89849f6c238ce1e5b70008612ae42cdd` | Apache-2.0 | 19 | 55,575,815,536 |
| Candidate B control | `Qwen/Qwen3.8-27B` | `1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0` | Apache-2.0 | 19 | 55,575,816,096 |

Candidate A declares `Qwen/Qwen3-30B-A3B-Instruct-2507` as its base model; Candidate B declares `Qwen/Qwen3.8-27B`.

## Pending gates

- Save the full model-card and license snapshots at the immutable revisions.
- Capture complete filename, byte-count, and LFS SHA-256 manifests for the selected initial candidate and its copied storage location.
- Validate copied files before promotion from `.uploading` storage.
- Define the evaluation pack, approved GPU budget, maximum hourly price, and shutdown deadline.

## Decision

Status remains `benchmark_required`. Candidate A stays the default first-run candidate because it is reported as already copied, but no artifact has been validated and no serving run may begin from this record alone.
