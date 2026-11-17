# Fusion Advantec — Junior DevSecOps Take-home

**Status: FAIL baseline verified on `main`; dependency remediation PR in progress.**

## Purpose
GitHub Actions on `push` to `main` and `pull_request` to `main` runs a pinned Trivy v0.66.0 filesystem dependency scan (`aquasec/trivy:0.66.0@sha256:086971aaf400beebd94e8300fd8ea623774419597169156cec56eec5b00dfb1e`), exports JSON, and applies a separate High/Critical quality gate (`scripts/quality_gate.py`). Scanner failures are never treated as PASS.

## Setup and reproducible evidence
1. From `sample-app/`, regenerate the lockfile with install scripts disabled:
   ```bash
   npm install --package-lock-only --ignore-scripts
   ```
   Commit `package-lock.json` (do not commit `node_modules/`).
2. **Baseline FAIL run**: Pushing the intentionally vulnerable dependency manifest (`axios@0.21.1`, `express@4.17.1`, `jsonwebtoken@8.5.1`, `lodash@4.17.20`, `minimist@0.0.8`) to `main` triggers Trivy and fails the quality gate (`exit 1`) on High/Critical findings while still uploading the raw JSON artifact.
3. **Dependency remediation (PASS strategy)**: On a remediation branch (`fix/remediate-dependencies`), upgrade the vulnerable dependencies to patched versions (`axios@^1.13.0`, `express@^4.21.2`, `jsonwebtoken@^9.0.2`, `lodash@^4.17.21`, `minimist@^1.2.8`), regenerate `sample-app/package-lock.json` with `--package-lock-only --ignore-scripts`, verify locally with Trivy and `scripts/quality_gate.py`, and open a Pull Request targeting `main` to verify the `pull_request` trigger and `GATE_PASS` (`exit 0`) without weakening security controls.
4. Store downloaded CI JSON artifacts in `results/` and redacted logs in `evidence/logs/`.

## Quality gate
`python3 scripts/quality_gate.py results/trivy.json` returns:
- `0`: zero High/Critical findings (`GATE_PASS`)
- `1`: one or more High/Critical findings (`GATE_FAIL`)
- `2`: missing, empty, malformed, or schema-invalid JSON (`SCAN_ERROR`)

The workflow runs the gate only when `steps.scan.outcome == 'success'` and uploads `results/trivy.json` with `if: always()`. Unit tests are in `tests/test_quality_gate.py` (`python3 -m unittest discover -s tests -v`).

## Design decisions and limitations
- **Pinning**: `aquasec/trivy:0.66.0` is pinned by verified `sha256` digest, and `actions/checkout` / `actions/upload-artifact` (`v4`) are pinned by full commit SHA.
- **Scope**: Dependency-only scanning (`--scanners vuln`) is not SAST and does not test running services, secrets, or infrastructure misconfigurations.
- **Database drift**: The Trivy vulnerability database updates over time, so scan counts can change by scan date. Always record scan timestamp, tool version, run URL, and commit SHA.
- **Pass semantics**: A PASS means zero High/Critical findings in this dependency scope at scan time, not proof of an application free of all security risks.
- Do not deploy intentionally vulnerable sample manifests publicly.

## AI assistance disclosure
Workflow hardening, quality-gate validation/tests, remediation verification, and documentation updates were prepared with AI assistance and independently validated via local tests, Dockerized Trivy scans, and GitHub Actions runs.

## Evidence manifest
| Run type | Commit SHA | Actions URL | JSON artifact | Verified gate outcome |
|---|---|---|---|---|
| FAIL (`push` to `main`) | `b319129715d45b2c736b2cc403cc8e2bcdc38e7d` | https://github.com/DerbSwag/fusion-devsecops-takehome/actions/runs/44021949406 | `results/run-fail-44021949406.json` (`trivy-json-44021949406-1`) | `GATE_FAIL` (`exit 1`: 1 Critical, 20 High, 21 Medium, 7 Low) |
| PASS (`pull_request` to `main`) | Pending PR CI verification | Pending PR CI verification | Pending PR CI verification | Pending PR CI verification |

## Reports
See `report/` for reporting templates. Complete only from verified GitHub Actions JSON artifacts.
