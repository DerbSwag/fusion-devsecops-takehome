# Fusion Advantec — Junior DevSecOps Take-home

**Status: Complete and verified on `main`. Historical FAIL (`main`), PASS (PR #1), hardening (PR #2), and final reports (PR #3) are all merged to `main` and verified by passing post-merge CI runs (`44027721027`, `44051483315`, and `44303024407`), with screenshots, JSON artifacts, logs, and both reports committed.**

## Purpose
GitHub Actions on `push` to `main` and `pull_request` to `main` runs a digest-pinned Trivy v0.66.0 filesystem dependency scan (`aquasec/trivy:0.66.0@sha256:086971aaf400beebd94e8300fd8ea623774419597169156cec56eec5b00dfb1e`), exports JSON, and applies a separate High/Critical quality gate (`scripts/quality_gate.py`). Scanner failures are never treated as PASS.

## Setup and reproducible evidence
1. From `sample-app/`, regenerate the lockfile with install scripts disabled:
   ```bash
   npm install --package-lock-only --ignore-scripts
   ```
   Commit `package-lock.json` (do not commit `node_modules/`).
2. **Baseline FAIL run**: Pushing the intentionally vulnerable manifest (`axios@0.21.1`, `express@4.17.1`, `jsonwebtoken@8.5.1`, `lodash@4.17.20`, `minimist@0.0.8`) to `main` triggers Trivy, detects 1 Critical / 20 High / 21 Medium / 7 Low findings, fails `scripts/quality_gate.py` with exit code `1`, and uploads the raw JSON artifact.
3. **Dependency remediation (PASS run)**: On branch `fix/remediate-dependencies` (PR [#1](https://github.com/DerbSwag/fusion-devsecops-takehome/pull/1), merged to `main` at `a32f03fd6fb6491230d6d41a678619b80195b955` with `main` CI run `44027721027` succeeding), the five dependencies were upgraded to patched versions (`axios@1.21.1`, `express@4.22.3`, `jsonwebtoken@9.0.3`, `lodash@4.18.1`, `minimist@1.2.8` in `package-lock.json`), triggering the `pull_request` workflow and passing `scripts/quality_gate.py` with exit code `0` (`0` findings across all severities) without weakening security controls.
4. Original CI JSON artifacts are preserved in `results/` and CI logs in `evidence/logs/`.
5. To reproduce the scan locally with Docker:
   ```bash
   docker run --rm -v "${PWD}/sample-app:/workspace:ro" -v "${PWD}/results:/output" \
     aquasec/trivy:0.66.0@sha256:086971aaf400beebd94e8300fd8ea623774419597169156cec56eec5b00dfb1e \
     fs --scanners vuln --format json --output /output/trivy-local.json --exit-code 0 /workspace
   python3 scripts/quality_gate.py results/trivy-local.json
   ```

## Quality gate
`python3 scripts/quality_gate.py results/trivy.json` returns:
- `0`: zero High/Critical findings (`GATE_PASS`)
- `1`: one or more High/Critical findings (`GATE_FAIL`)
- `2`: missing, empty, malformed, schema-invalid JSON, or missing expected npm lockfile target (`SCAN_ERROR`)

The workflow runs unit tests before scanning, runs the gate only when `steps.scan.outcome == 'success'`, and uploads `results/trivy.json` with `if: always()`. The gate verifies that Trivy inspected the expected `package-lock.json` npm target; missing or unrelated targets fail closed rather than returning a false PASS. Unit tests are in `tests/test_quality_gate.py` (`python3 -m unittest discover -s tests -v`).

## Design decisions and limitations
- **Pinning**: `aquasec/trivy:0.66.0` is pinned by verified `sha256` digest (`sha256:086971aaf400beebd94e8300fd8ea623774419597169156cec56eec5b00dfb1e`), and `actions/checkout` (`11d5960a326750d5838078e36cf38b85af677262`) and `actions/upload-artifact` (`ea165f8d65b6e75b540449e92b4886f43607fa02`) are pinned by full commit SHA.
- **Scope**: Dependency-only scanning (`--scanners vuln` on `/workspace/sample-app`, covering `package-lock.json`) is not SAST and does not test running services, secrets, or infrastructure misconfigurations.
- **Database drift**: The Trivy vulnerability database updates over time, so scan counts can change by scan date. Always record scan timestamp, tool version, run URL, and commit SHA.
- **Pass semantics**: A PASS means Trivy scanned the expected npm lockfile and reported zero High/Critical findings within this dependency scope, not proof of an application free of all security risks.
- **Historical vs current state**: The FAIL artifact was captured on vulnerable `main` before PR #1; the PASS artifact was captured on PR #1 before merge. PR #1 (remediation), PR #2 (hardening), and PR #3 (final reports) are all merged to `main` and independently verified by passing post-merge runs ([44027721027](https://github.com/DerbSwag/fusion-devsecops-takehome/actions/runs/44027721027), [44051483315](https://github.com/DerbSwag/fusion-devsecops-takehome/actions/runs/44051483315), and [44303024407](https://github.com/DerbSwag/fusion-devsecops-takehome/actions/runs/44303024407)). Historical screenshots, JSON, and logs remain unchanged.
- **Hardened validation**: Target-validation logic and all 14 quality-gate unit tests were merged in PR #2 and verified in post-merge `main` CI runs (`44051483315` and `44303024407`).
- Do not deploy intentionally vulnerable sample manifests publicly.

## AI assistance disclosure
Workflow hardening, quality-gate validation/tests, remediation verification, and documentation updates were prepared with AI assistance and independently verified via local unit tests, Dockerized Trivy scans, and real GitHub Actions runs.

## Evidence manifest
| Run type | Trigger | Commit SHA | Actions URL | Artifact name & local path | Verified gate outcome |
|---|---|---|---|---|---|
| FAIL | `push` (`main`) | `b319129715d45b2c736b2cc403cc8e2bcdc38e7d` | https://github.com/DerbSwag/fusion-devsecops-takehome/actions/runs/44021949406 | `trivy-json-44021949406-1` (`results/run-fail-44021949406.json`) | `GATE_FAIL` (`exit 1`: Critical 1, High 20, Medium 21, Low 7) |
| PASS | `pull_request` (PR #1, merged) | `dbcfa10513c98872961ee933f0da5dc7dc529be8` | https://github.com/DerbSwag/fusion-devsecops-takehome/actions/runs/44024570812 | `trivy-json-44024570812-1` (`results/run-pass-44024570812.json`) | `GATE_PASS` (`exit 0`: Critical 0, High 0, Medium 0, Low 0) |
| Post-merge (PR #1) | `push` (`main`) | `a32f03fd6fb6491230d6d41a678619b80195b955` | https://github.com/DerbSwag/fusion-devsecops-takehome/actions/runs/44027721027 | — (post-merge verification run) | `success` |
| Post-merge (PR #2) | `push` (`main`) | `61609d4c245829c4a1de16851ca44a28cf1d3144` | https://github.com/DerbSwag/fusion-devsecops-takehome/actions/runs/44051483315 | `trivy-json-44051483315-1` (CI artifact) | `GATE_PASS` (`exit 0`, 14/14 unit tests) |
| Post-merge (PR #3) | `push` (`main`) | `d6ac87f0516f40b5cd0b7e5664eaf4c846cc52d8` | https://github.com/DerbSwag/fusion-devsecops-takehome/actions/runs/44303024407 | `trivy-json-44303024407-1` (CI artifact) | `GATE_PASS` (`exit 0`, 14/14 unit tests) |

## Reports & evidence files
- **Executive Summary**: [report/executive-summary.md](report/executive-summary.md)
- **Technical Report**: [report/technical-report.md](report/technical-report.md)
- **CI Screenshots**: [evidence/run-fail.png](evidence/run-fail.png) and [evidence/run-pass.png](evidence/run-pass.png)
- **CI Logs**: [evidence/logs/run-fail-44021949406.log](evidence/logs/run-fail-44021949406.log) and [evidence/logs/run-pass-44024570812.log](evidence/logs/run-pass-44024570812.log)
