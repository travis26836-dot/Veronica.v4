# T2 pinned-license and lineage review

Status: documented for evaluation preparation; not legal advice and not model qualification.

## Scope

The model cards and license files were captured from each immutable revision with the Hugging Face CLI. The local SHA-256 values are recorded in `provenance-manifest.json`.

| Role | Repository | Revision | Declared license | Repository NOTICE file |
| --- | --- | --- | --- | --- |
| Candidate A | `huihui-ai/Huihui-Qwen3-30B-A3B-Instruct-2507-abliterated` | `e2f73ec7e99ee316beb8069ca90e4c3cbef8aa0f` | Apache-2.0 | None listed |
| Candidate A control | `Qwen/Qwen3-30B-A3B-Instruct-2507` | `0d7cf23991f47feeb3a57ecb4c9cee8ea4a17bfe` | Apache-2.0 | None listed |
| Candidate B | `huihui-ai/Huihui-Qwen3.8-27B-abliterated` | `739e3c5b89849f6c238ce1e5b70008612ae42cdd` | Apache-2.0 | None listed |
| Candidate B control | `Qwen/Qwen3.8-27B` | `1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0` | Apache-2.0 | None listed |

The repository file listings were checked at those exact revisions. All four contain `LICENSE`; none lists `NOTICE`. This finding applies only to the captured revisions.

## License permissions and obligations

The captured files contain the standard Apache License 2.0 text. Subject to its terms, it grants copyright permission to reproduce, prepare derivative works, display, sublicense and distribute the work, and it grants a patent license from contributors. The Apache Software Foundation FAQ states that the license does not distinguish commercial from personal or internal use.

For redistribution, preserve a copy of the license, mark modified files, retain applicable copyright/patent/trademark/attribution notices, and carry forward any qualifying NOTICE content if one exists. The license does not grant trademark rights, includes warranty/liability disclaimers, and terminates its patent grant for the work when the licensee initiates specified patent litigation.

No separate repository NOTICE file was present, but a release must repeat this check against the exact artifacts being distributed and retain any notices embedded in source files or later-added dependencies.

Primary references:

- `https://www.apache.org/licenses/LICENSE-2.0`
- `https://www.apache.org/foundation/license-faq.html`
- The eight pinned local snapshots under `provenance/`

## Lineage and modification method

- Candidate A names `Qwen/Qwen3-30B-A3B-Instruct-2507` as its base and describes itself as an abliterated derivative. Its card calls the implementation a crude proof of concept.
- Candidate B names `Qwen/Qwen3.8-27B` as its base and describes abliteration of layers 18 through 51. Its card states that MTP and visual components were not modified.
- Those are repository-author declarations. They do not independently prove uploader authority, training-data rights, absence of third-party restrictions, or capability preservation.

## Gate decision

The pinned card/license snapshot, declared commercial/modification/redistribution permissions, attribution obligations, base lineage and stated ablation method are documented for all four entries. Weight integrity, runtime compatibility and capability comparison remain separate open gates.

