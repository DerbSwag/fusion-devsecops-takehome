# Fusion Advantec — Junior DevSecOps Take-home (starter)

**Status: NOT EXECUTED.** This starter contains no real CI evidence or scan findings. Never claim a PASS or FAIL without linking an actual GitHub Actions run and its downloaded JSON artifact.

## Purpose
GitHub Actions on `push` to `main` and `pull_request` to `main` runs a version-fixed Trivy filesystem dependency scan, saves JSON, then applies a separate High/Critical quality gate. Scanner failure is not treated as PASS. No secrets required for this public vulnerability-only sample.

## Setup and reproducible evidence
1. Create a NEW repository under your own account. Do not add credentials. Review every file.
2. From `sample-app/`, run `npm install --package-lock-only --ignore-scripts` on your own machine. Commit `package-lock.json` (do not commit `node_modules`). This is required for reliable dependency detection.
3. Push the intentionally vulnerable manifest/lockfile to `main` and capture the **real failing run** URL, screenshot, logs, and artifact JSON. Check the actual gate message and findings. If the scanner errors instead, troubleshoot; it is NOT valid gate-fail evidence.
4. For a **passing run**, replace the vulnerable dependencies with an empty dependency map in `sample-app/package.json`, regenerate lockfile (`npm install --package-lock-only --ignore-scripts`), commit/push to `main`, and verify the real gate pass. This is a *clean test fixture*, not remediation of the vulnerable application. Record that limitation.
5. Open a PR against `main` with an authorized test change to demonstrate the PR trigger. Verify the scan actually ran.
6. Download artifacts from each run; place the original JSON in `results/` with distinct names, and redact logs before storing them in `evidence/logs/`. Capture actual screenshots as `evidence/run-fail.png` and `evidence/run-pass.png`.
7. Create reports based ONLY on real JSON; counts must reconcile to the exact scan artifact and run/commit SHA. Do not fabricate five findings or false positives.

## Quality gate
`python3 scripts/quality_gate.py results/trivy.json` returns 0 for zero High/Critical, 1 for findings, and 2 for missing/invalid data. The workflow fails if scanner exits nonzero, even if a JSON file exists. Artifacts upload with `if: always()`.

## Design decisions and limitations
- Trivy v0.66.0 is fixed to a release tag; production hardening should pin the container image by verified digest and pin GitHub Actions by full commit SHA. Tags are not immutable.
- `actions/checkout@v4` and `actions/upload-artifact@v4` are major-version tags, not full-SHA pins; improve before final submission if feasible.
- Dependency-only scanning (`--scanners vuln`) is not SAST and does not test running services, secrets, or misconfigurations.
- Trivy vulnerability database is updated over time: results can differ by scan date. Store scan timestamp, tool version, run URL, and commit SHA.
- A pass means no High/Critical findings **in this scan scope at that time**, not proof of a secure application.
- Avoid deploying intentionally vulnerable sample applications to the internet.

## AI assistance disclosure
Initial workflow, quality gate, sample manifest, and README were drafted with AI assistance. Candidate must review, test, understand, and revise each component before submitting. Actual runs, findings, screenshots, and reports must be independently verified.

## Evidence manifest (fill after real execution)
| Run type | Commit SHA | Actions URL | JSON artifact | Verified gate outcome |
|---|---|---|---|---|
| FAIL | TBD | TBD | TBD | TBD |
| PASS | TBD | TBD | TBD | TBD |

## Reports
See `report/` for reporting templates. Complete only after collecting real scan artifacts.
