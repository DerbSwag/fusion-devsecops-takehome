# Technical Security Report — Fusion Advantec Take-Home

## 1. Scanner and CI Environment
- **Repository**: `DerbSwag/fusion-devsecops-takehome`
- **CI Platform**: GitHub Actions (`ubuntu-24.04`, `timeout-minutes: 20`, `permissions: contents: read`)
- **Scanner**: Trivy `v0.66.0` (`aquasec/trivy:0.66.0@sha256:086971aaf400beebd94e8300fd8ea623774419597169156cec56eec5b00dfb1e`)
- **Pinned Actions**: `actions/checkout@11d5960a326750d5838078e36cf38b85af677262` (`v4`), `actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02` (`v4`)
- **Quality Gate**: `scripts/quality_gate.py` (Python 3; exits `0` for zero High/Critical, `1` for High/Critical findings, `2` for missing/empty/malformed scan data)
- **FAIL Baseline Run**: `push` to `main` — Commit `b319129715d45b2c736b2cc403cc8e2bcdc38e7d`, Run `44021949406` (2026-11-17T05:08:38Z)
- **PASS Remediation Run**: `pull_request` (PR #1, now merged) — Commit `dbcfa10513c98872961ee933f0da5dc7dc529be8`, Run `44024570812` (2026-11-17T05:30:43Z)

- **Post-Merge main PASS**: Commit `a32f03fd6fb6491230d6d41a678619b80195b955`, [Run 44027721027](https://github.com/DerbSwag/fusion-devsecops-takehome/actions/runs/44027721027) (0 Critical / High / Medium / Low findings, verified from CI logs). This is distinct from the archived PR PASS artifact.
- **Submission-hardening branch**: `fix/final-submission-hardening-20261117`; additional target validation and CI unit tests are subject to new CI verification.

## 2. Scan Scope and Limitations
- **Scope**: Filesystem dependency vulnerability scan (`trivy fs --scanners vuln --format json`) targeting `/workspace/sample-app` (`sample-app/package-lock.json`, `lang-pkgs` / `npm`).
- **Limitations**:
  - Lockfile-only SCA does **not** perform SAST, secret detection, IaC/container scanning, or dynamic runtime testing.
  - Trivy matches package versions in `package-lock.json` against its vulnerability DB; it does not verify code-path reachability.
  - Vulnerability DB contents change over time; results reflect the DB state at each run's timestamp.

## 3. Finding Counts by Severity (FAIL Baseline — Run `44021949406`)
| Scanner | Target | Critical | High | Medium | Low | Unknown | Total |
|---|---|---:|---:|---:|---:|---:|---:|
| Trivy `0.66.0` | `package-lock.json` | 1 | 20 | 21 | 7 | 0 | 49 |

## 4. Top Real Issues from `results/run-fail-44021949406.json`
| Priority | ID (CVE / CWE) | Package & Installed Version | Fixed Version(s) | Impact (from Trivy DB) | Remediation |
|---|---|---|---|---|---|
| **P1 (Critical)** | `CVE-2021-44906` (`CWE-1321`) | `minimist@0.0.8` | `1.2.6`, `0.2.4` | Prototype pollution allowing property injection into `Object.prototype` | Upgrade `minimist` to `^1.2.8` |
| **P2 (High)** | `CVE-2021-23337`, `CVE-2026-4800` (`CWE-94`) | `lodash@4.17.20` | `4.17.21`, `4.18.0` | Command injection / arbitrary code execution via `template` | Upgrade `lodash` to `^4.17.21` (resolved `4.18.1`) |
| **P2 (High)** | `CVE-2025-27152` (`CWE-918`) | `axios@0.21.1` | `1.8.2`, `0.30.0` | Possible SSRF and credential leakage via absolute URLs in requests | Upgrade `axios` to `^1.13.0` (resolved `1.21.1`) |
| **P2 (High)** | `CVE-2022-23539` (`CWE-327`) | `jsonwebtoken@8.5.1` | `9.0.0` | Unrestricted key type allowing legacy/weak key usage | Upgrade `jsonwebtoken` to `^9.0.2` (resolved `9.0.3`) |
| **P2 (High)** | `CVE-2024-45590` (`CWE-405`), `CVE-2024-45296` (`CWE-1333`), `CVE-2022-24999` (`CWE-1321`) | `body-parser@1.19.0`, `path-to-regexp@0.1.7`, `qs@6.7.0` (transitive via `express@4.17.1`) | `body-parser` `1.20.3`, `path-to-regexp` `0.1.10+`, `qs` `6.2.4+` | Denial of Service / ReDoS / prototype poisoning hanging Node.js | Upgrade `express` to `^4.21.2` (resolved `4.22.3`, updating transitive deps) |

## 5. Practical Remediation & Prioritization Rationale
1. **Priority 1 — Direct & Transitive Critical/RCE/Auth Flaws (`minimist`, `lodash`, `jsonwebtoken`)**: `CVE-2021-44906` (`CRITICAL`) and `CWE-94` / `CWE-327` carry the highest potential blast radius (prototype pollution, code execution, JWT validation weakness) and are remediated cleanly via dependency upgrades.
2. **Priority 2 — HTTP Client & Web Framework High Findings (`axios`, `express` transitives)**: `axios@0.21.1` accounts for 24 of the 49 findings (including SSRF, prototype pollution, and proxy credential leaks); upgrading `axios` and `express` resolves both direct and transitive (`body-parser`, `path-to-regexp`, `qs`) High/Medium/Low findings.
3. **Priority 3 — Medium/Low Findings**: Resolved as part of the `axios` and `express` upgrades above.

## 6. Potential False Positives / Lower-Risk Assessments
*Note: Trivy reports package-version presence in `package-lock.json`, not validated runtime exploitability.*

1. **`CVE-2021-23337` / `CVE-2026-4800` (`lodash@4.17.20`, High, `CWE-94`)**:
   - **Evidence**: Flagged in `package-lock.json` (`lodash@4.17.20`).
   - **Context & Reason**: Exploitation requires calling `_.template()` with untrusted input. `sample-app/` contains only `package.json` and `package-lock.json` with no application source code invoking `_.template()`.
   - **Residual Risk & Validation**: Low immediate exploitability in the current fixture, but latent risk if future code uses `_.template()`. Validated by upgrading `lodash` to `4.18.1`.
2. **`CVE-2026-44486` / `CVE-2026-44487` (`axios@0.21.1`, High, `CWE-200`/`CWE-201`)**:
   - **Evidence**: Flagged in `package-lock.json` (`axios@0.21.1`).
   - **Context & Reason**: Proxy credential disclosure requires `axios` to be configured with proxy credentials and to follow untrusted HTTP redirects. Without runtime/code context, exploitability is unvalidated.
   - **Residual Risk & Validation**: Eliminated by upgrading `axios` to `1.21.1` and confirming 0 findings in CI.

## 7. Before / After Scan Comparison
| Metric | Before (FAIL — Run `44021949406`) | After (PASS — Run `44024570812`) |
|---|---:|---:|
| Critical | 1 | 0 |
| High | 20 | 0 |
| Medium | 21 | 0 |
| Low | 7 | 0 |
| **Total** | **49** | **0** |
| Quality Gate (`quality_gate.py`) | `GATE_FAIL` (`exit 1`) | `GATE_PASS` (`exit 0`) |

## 8. Original CI Evidence Links
- **FAIL Run**: https://github.com/DerbSwag/fusion-devsecops-takehome/actions/runs/44021949406
  - Artifact: `trivy-json-44021949406-1` (ZIP `sha256:93db588034c1763762531c5914a86efac1f99f826b19ea84fd1e385cfc6dad06`; extracted `results/run-fail-44021949406.json` `sha256:1e3caa9f9e380172f7b7c624a74153c2e710d976858da44bb5c2cfc5e48024a3`)
  - Log: `evidence/logs/run-fail-44021949406.log`
- **PASS Run (PR #1)**: https://github.com/DerbSwag/fusion-devsecops-takehome/actions/runs/44024570812
  - Artifact: `trivy-json-44024570812-1` (ZIP `sha256:51597a8c8bd4b64f62d44ac1a35ab9e778cd8cd03fcd91947bdb5faafee79432`; extracted `results/run-pass-44024570812.json` `sha256:50a35a151d877789ed41f572f797d8abee9f780f5442e8ef4924a6562c9395e3`)
  - Log: `evidence/logs/run-pass-44024570812.log`
