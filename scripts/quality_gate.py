#!/usr/bin/env python3
"""Evaluate Trivy JSON; fail closed on missing/invalid data."""
import json
import sys
from pathlib import Path

SEVERITIES = ("CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN")


def _validate_report(data: object) -> list[dict]:
    """Validate Trivy JSON report structure and return its Results list."""
    if not isinstance(data, dict):
        raise ValueError("Trivy report root must be a JSON object")

    schema_version = data.get("SchemaVersion")
    if isinstance(schema_version, bool) or not isinstance(schema_version, int):
        raise ValueError("Trivy SchemaVersion missing or invalid")

    if not isinstance(data.get("ArtifactName"), str) or not data["ArtifactName"]:
        raise ValueError("Trivy ArtifactName missing or invalid")
    if not isinstance(data.get("ArtifactType"), str) or not data["ArtifactType"]:
        raise ValueError("Trivy ArtifactType missing or invalid")

    # Trivy omits "Results" when 0 language-specific files/targets are found (e.g. empty dependencies).
    if "Results" not in data:
        return []

    results = data["Results"]
    if not isinstance(results, list):
        raise ValueError("Trivy Results must be an array")
    return results


def evaluate(path: Path) -> int:
    """Return 0 for zero High/Critical, 1 for findings, 2 for missing/invalid data."""
    if not path.is_file() or path.stat().st_size == 0:
        print("SCAN_ERROR: missing or empty JSON")
        return 2
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        results = _validate_report(data)
        counts = {key: 0 for key in SEVERITIES}
        for result in results:
            if not isinstance(result, dict):
                raise ValueError("Trivy Result entry must be an object")
            vulns = result.get("Vulnerabilities")
            if vulns is None:
                continue
            if not isinstance(vulns, list):
                raise ValueError("Trivy Vulnerabilities must be an array or null")
            for vuln in vulns:
                if not isinstance(vuln, dict):
                    raise ValueError("Trivy Vulnerability entry must be an object")
                raw_sev = vuln.get("Severity")
                severity = raw_sev.strip().upper() if isinstance(raw_sev, str) else "UNKNOWN"
                counts[severity if severity in counts else "UNKNOWN"] += 1

        print("FINDINGS " + " ".join(f"{s}={counts[s]}" for s in SEVERITIES))
        blocking = counts["HIGH"] + counts["CRITICAL"]
        if blocking:
            print(f"GATE_FAIL: {blocking} High/Critical finding(s)")
            return 1
        print("GATE_PASS: zero High/Critical findings")
        return 0
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        print(f"SCAN_ERROR: invalid scan data: {exc}")
        return 2


if __name__ == "__main__":
    sys.exit(evaluate(Path(sys.argv[1])) if len(sys.argv) == 2 else 2)
