# Technical Security Report — Fusion Advantec Take-Home

## 1. Scanner Coverage and CI Environment

- **Repository**: `DerbSwag/fusion-devsecops-takehome` (`PUBLIC`, default branch `main`)
- **CI Platform**: GitHub Actions (`ubuntu-24.04`, `timeout-minutes: 20`, `permissions: contents: read`)
- **Scanner**: Trivy `v0.66.0` (`aquasec/trivy:0.66.0@sha256:086971aaf400beebd94e8300fd8ea623774419597169156cec56eec5b00dfb1e`)
- **Pinned Actions**: `actions/checkout@11d5960a326750d5838078e36cf38b85af677262` (`v4`, `persist-credentials: false`), `actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02` (`v4`, `retention-days: 14`)
- **Target and Scan Type**: Filesystem Software Composition Analysis (SCA) (`trivy fs --scanners vuln --format json --output /output/trivy.json --exit-code 0 /workspace/sample-app`) inspecting `sample-app/package-lock.json` (`Class: lang-pkgs`, `Type: npm`).
- **Quality Gate**: `scripts/quality_gate.py` (Python 3; exits `0` for zero High/Critical findings, `1` for one or more High/Critical findings, `2` for missing, empty, malformed, schema-invalid JSON, or missing expected `package-lock.json` npm target).
- **CI Run History**:
  - **Historical FAIL Baseline (`main`)**: Run [`44021949406`](https://github.com/DerbSwag/fusion-devsecops-takehome/actions/runs/44021949406) (`push`, commit `b319129715d45b2c736b2cc403cc8e2bcdc38e7d`, `2026-11-17T05:08:38Z`) — `GATE_FAIL` (`exit 1`).
  - **Historical PASS Remediation (PR #1)**: Run [`44024570812`](https://github.com/DerbSwag/fusion-devsecops-takehome/actions/runs/44024570812) (`pull_request`, commit `dbcfa10513c98872961ee933f0da5dc7dc529be8`, `2026-11-17T05:30:43Z`) — `GATE_PASS` (`exit 0`).
  - **Post-Merge `main` (PR #1)**: Run [`44027721027`](https://github.com/DerbSwag/fusion-devsecops-takehome/actions/runs/44027721027) (`push`, commit `a32f03fd6fb6491230d6d41a678619b80195b955`, `2026-11-17T05:57:45Z`) — `success`.
  - **Latest Verified Post-Merge `main` (PR #2)**: Run [`44051483315`](https://github.com/DerbSwag/fusion-devsecops-takehome/actions/runs/44051483315) (`push`, commit `61609d4c245829c4a1de16851ca44a28cf1d3144`, `2026-11-17T08:59:45Z`, artifact `trivy-json-44051483315-1` ID `14314006995`) — `success`, 14/14 unit tests passed, `GATE_PASS` (`exit 0`, 0 findings).

### Finding Totals by Scanner and Severity

| Scanner | Target | Scan State | Critical | High | Medium | Low | Unknown | Total | Gate Result |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| Trivy `0.66.0` | `package-lock.json` (`npm`) | Historical FAIL (`44021949406`) | 1 | 20 | 21 | 7 | 0 | **49** | `GATE_FAIL` (`exit 1`) |
| Trivy `0.66.0` | `package-lock.json` (`npm`) | Historical PASS (`44024570812`) | 0 | 0 | 0 | 0 | 0 | **0** | `GATE_PASS` (`exit 0`) |
| Trivy `0.66.0` | `package-lock.json` (`npm`) | Latest Post-Merge `main` (`44051483315`) | 0 | 0 | 0 | 0 | 0 | **0** | `GATE_PASS` (`exit 0`) |

### Scope Limitations

Dependency SCA on `sample-app/package-lock.json` **does not establish complete application security**:
- **No SAST, DAST, Secret, or IaC Coverage**: `--scanners vuln` on `sample-app/` does not inspect application source code, hardcoded secrets, container images, or infrastructure configurations.
- **No Reachability Analysis**: Trivy matches locked package versions against its vulnerability database; it does not determine whether vulnerable functions are invoked at runtime.
- **Database Drift**: Vulnerability database contents change as new CVEs are published; zero findings reflects the Trivy DB state at each run's timestamp.

---

## 2. Top Findings (`results/run-fail-44021949406.json`)

The baseline scan detected 49 vulnerabilities across 11 packages (`axios` 24, `qs` 5, `lodash` 4, `body-parser` 3, `jsonwebtoken` 3, `path-to-regexp` 3, `express` 2, `minimist` 2, `cookie` 1, `send` 1, `serve-static` 1). The seven highest-risk packages containing Critical/High findings are detailed below:

| Priority & Severity | Package (Scope) | CVE / CWE | Installed | Scanner Fixed Version(s) | Resolved Version (`package-lock.json`) | Security Impact (per Trivy DB) | Remediation Performed | Evidence |
|---|---|---|---|---|---|---|---|---|
| **P1 — Critical** | `minimist` (direct) | `CVE-2021-44906` (`CWE-1321`) | `0.0.8` | `1.2.6`, `0.2.4` | `1.2.8` | Prototype pollution allowing property injection into `Object.prototype` | Upgraded `minimist` to `^1.2.8` in `sample-app/package.json` | `results/run-fail-44021949406.json`, `sample-app/package-lock.json` |
| **P2 — High** | `lodash` (direct) | `CVE-2021-23337`, `CVE-2026-4800` (`CWE-94`) | `4.17.20` | `4.17.21`, `4.18.0` | `4.18.1` | Command injection / arbitrary code execution via `_.template()` | Upgraded `lodash` to `^4.17.21` in `sample-app/package.json` | `results/run-fail-44021949406.json`, `sample-app/package-lock.json` |
| **P2 — High** | `jsonwebtoken` (direct) | `CVE-2022-23539` (`CWE-327`) | `8.5.1` | `9.0.0` | `9.0.3` | Unrestricted key type allowing legacy/weak cryptographic key usage | Upgraded `jsonwebtoken` to `^9.0.2` in `sample-app/package.json` | `results/run-fail-44021949406.json`, `sample-app/package-lock.json` |
| **P2 — High** | `axios` (direct) | `CVE-2021-3749` (`CWE-1333`, `CWE-400`), `CVE-2025-27152` (`CWE-918`), `CVE-2026-25639` (`CWE-754`, `CWE-1287`), `CVE-2026-42033` (`CWE-1321`, `CWE-915`), `CVE-2026-42035` (`CWE-113`, `CWE-1321`), plus 6 additional High CVEs | `0.21.1` | `0.21.2`–`1.16.0` (varies by CVE; `1.16.0` / `0.32.0` latest) | `1.21.1` | ReDoS, SSRF, credential leakage, HTTP transport/header injection, and DoS via `__proto__` (24 total findings) | Upgraded `axios` to `^1.13.0` in `sample-app/package.json` | `results/run-fail-44021949406.json`, `sample-app/package.json` |
| **P2 — High** | `body-parser` (transitive via `express`) | `CVE-2024-45590` (`CWE-405`), `CVE-2026-111181` (`CWE-248`) | `1.19.0` | `1.20.3`, `2.4.0`, `1.20.9` | `1.20.9` | Denial of Service via malformed payloads and unhandled decompression stream error | Upgraded `express` to `^4.21.2` (`4.22.3` resolved), updating transitive `body-parser` | `results/run-fail-44021949406.json`, `sample-app/package-lock.json` |
| **P2 — High** | `path-to-regexp` (transitive via `express`) | `CVE-2024-45296`, `CVE-2024-52798`, `CVE-2026-4867` (`CWE-1333`) | `0.1.7` | `0.1.10`, `0.1.12`, `0.1.13` (0.1.x branch) | `0.1.13` | Regular Expression Denial of Service (ReDoS) via backtracking on malformed route/URL parameters | Upgraded `express` to `^4.21.2` (`4.22.3` resolved), updating transitive `path-to-regexp` | `results/run-fail-44021949406.json`, `sample-app/package-lock.json` |
| **P2 — High** | `qs` (transitive via `express`) | `CVE-2022-24999` (`CWE-1321`) | `6.7.0` | `6.10.3`, `6.7.3` (and patched branches) | `6.16.2` | Prototype poisoning causing Node.js process hang / Denial of Service | Upgraded `express` to `^4.21.2` (`4.22.3` resolved), updating transitive `qs` | `results/run-fail-44021949406.json`, `sample-app/package-lock.json` |

---

## 3. Risk-Based Prioritization Rationale

Remediation order was determined by combining severity with operational risk factors rather than CVSS score alone:

1. **Priority 1 — Direct Critical / RCE / Auth Flaws (`minimist`, `lodash`, `jsonwebtoken`)**:
   - **Severity & Exploitability**: `CVE-2021-44906` (`CRITICAL`) and `CWE-94`/`CWE-327` affect core argument parsing, utility templating, and JWT signature/key validation.
   - **Business Impact & Blast Radius**: Successful exploitation can alter global object prototypes, execute arbitrary commands, or weaken authentication token verification.
   - **Ease & Risk of Remediation**: Direct version bumps in `package.json` (`minimist@^1.2.8`, `lodash@^4.17.21`, `jsonwebtoken@^9.0.2`) carry low integration risk when lockfiles are regenerated cleanly.
2. **Priority 2 — High-Exposure HTTP Client & Web Framework Transitives (`axios`, `express` -> `body-parser`, `path-to-regexp`, `qs`)**:
   - **Exposure & Prerequisites**: `express` request-parsing and routing middleware sits directly on external HTTP ingress, making ReDoS and decompression DoS reachable by unauthenticated remote requests. `axios@0.21.1` accounted for 24 of 49 findings (nearly half of all baseline alerts), including SSRF and header injection.
   - **Blast Radius & Ease of Remediation**: Upgrading `express` to `^4.21.2` (`4.22.3` resolved) and `axios` to `^1.13.0` (`1.21.1` resolved) eliminated all transitive `body-parser`, `path-to-regexp`, and `qs` High findings in one coordinated lockfile update.
3. **Priority 3 — Remaining Medium/Low Findings (`cookie`, `send`, `serve-static`, and lower-severity `axios`/`express` items)**:
   - Resolved concurrently through the `axios` and `express` upgrades without requiring separate dependency overrides.

---

## 4. False-Positive and Lower-Risk Assessments

*Note: Neither assessment below classifies a confirmed vulnerable dependency version as a proven false positive; both distinguish confirmed package-version presence from unverified runtime exploitability.*

### 4.1 `lodash@4.17.20` — `CVE-2021-23337` & `CVE-2026-4800` (High, `CWE-94`)
- **Confirmed Scanner Finding**: `results/run-fail-44021949406.json` confirmed `lodash@4.17.20` in `sample-app/package-lock.json`.
- **Exploit Prerequisites**: Attacker-controlled input must reach `_.template()` (or template imports).
- **Available Evidence & Missing Context**: `sample-app/` contains only `package.json` and `package-lock.json`; no application source code or runtime telemetry exists in this repository to show whether `_.template()` is called.
- **Classification**: **Confirmed vulnerable dependency with unverified exploitability** (not a proven false positive).
- **Residual Risk & Validation**: Latent RCE risk if future application code introduces `_.template()` usage. Remediated and validated by upgrading `lodash` to `4.18.1` and confirming 0 findings in CI.

### 4.2 `axios@0.21.1` — `CVE-2026-44486` (`CWE-200`, `CWE-201`) & `CVE-2026-44487` (`CWE-201`) (High)
- **Confirmed Scanner Finding**: `results/run-fail-44021949406.json` confirmed `axios@0.21.1` in `sample-app/package-lock.json`.
- **Exploit Prerequisites**: The application must configure `axios` with proxy credentials and issue requests that follow untrusted HTTP redirects.
- **Available Evidence & Missing Context**: No runtime configuration, outbound HTTP client code, or proxy setup is present in `sample-app/` to confirm whether proxy credentials are used.
- **Classification**: **Confirmed vulnerable dependency with unverified exploitability** (not a proven false positive).
- **Residual Risk & Validation**: Eliminated at the dependency layer by upgrading `axios` to `1.21.1` and verifying zero Trivy findings in CI; outbound request policies should still be reviewed when application code is added.

---

## 5. Remediation Validation and Unresolved Risks

### Before / After Scan Comparison

| Metric | Historical FAIL (`44021949406`) | Historical PASS (`44024570812`) | Latest Post-Merge `main` (`44051483315`) |
|---|---:|---:|---:|
| Commit SHA | `b319129715d45b2c736b2cc403cc8e2bcdc38e7d` | `dbcfa10513c98872961ee933f0da5dc7dc529be8` | `61609d4c245829c4a1de16851ca44a28cf1d3144` |
| Critical | 1 | 0 | 0 |
| High | 20 | 0 | 0 |
| Medium | 21 | 0 | 0 |
| Low | 7 | 0 | 0 |
| **Total** | **49** | **0** | **0** |
| Quality Gate (`scripts/quality_gate.py`) | `GATE_FAIL` (`exit 1`) | `GATE_PASS` (`exit 0`) | `GATE_PASS` (`exit 0`) |

### Controls, Unit Tests, and Unresolved Risks
- **Fail-Closed Quality Gate & Unit Tests**: `scripts/quality_gate.py` only evaluates when `steps.scan.outcome == 'success'` and fails closed (`exit 2`) if `SchemaVersion`, `ArtifactName`, `ArtifactType`, `Results`, or the `package-lock.json` (`lang-pkgs`/`npm`) target is missing. All 14 unit tests in `tests/test_quality_gate.py` pass in CI (`44051483315`) and locally (`0.163s`).
- **Unresolved Risks & Limitations**:
  1. **Branch Protection Disabled**: GitHub API inspection confirms `main` branch protection is not active (`HTTP 404: Branch not protected`), so `security-scan` is not yet enforced as a mandatory merge gate.
  2. **SCA-Only Scope**: SAST, secret scanning, and scheduled CVE rescanning are not yet implemented.
  3. **Action Runtime Deprecation Warning**: `actions/checkout` and `actions/upload-artifact` v4 emit a Node.js 20 deprecation warning on GitHub-hosted runners.

---

## 6. Original CI Evidence Links

- **Historical FAIL Run (`main`)**: https://github.com/DerbSwag/fusion-devsecops-takehome/actions/runs/44021949406
  - Artifact: `trivy-json-44021949406-1` (extracted `results/run-fail-44021949406.json`, LF `sha256:1e3caa9f9e380172f7b7c624a74153c2e710d976858da44bb5c2cfc5e48024a3`)
  - Log: `evidence/logs/run-fail-44021949406.log`
- **Historical PASS Run (PR #1)**: https://github.com/DerbSwag/fusion-devsecops-takehome/actions/runs/44024570812
  - Artifact: `trivy-json-44024570812-1` (extracted `results/run-pass-44024570812.json`, LF `sha256:50a35a151d877789ed41f572f797d8abee9f780f5442e8ef4924a6562c9395e3`)
  - Log: `evidence/logs/run-pass-44024570812.log`
- **Latest Post-Merge `main` Run (PR #2)**: https://github.com/DerbSwag/fusion-devsecops-takehome/actions/runs/44051483315
  - Artifact: `trivy-json-44051483315-1` (Artifact ID `14314006995`, 327 bytes)
