"""Unit tests for scripts/quality_gate.py."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.quality_gate import evaluate

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "quality_gate.py"


def _base_report(**extra: object) -> dict:
    report = {
        "SchemaVersion": 2,
        "CreatedAt": "2026-11-17T04:55:19Z",
        "ArtifactName": "/workspace/sample-app",
        "ArtifactType": "filesystem",
    }
    report.update(extra)
    return report


class QualityGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp_dir = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _write_json(self, name: str, payload: object) -> Path:
        target = self.tmp_dir / name
        target.write_text(json.dumps(payload), encoding="utf-8")
        return target

    def test_high_and_critical_findings_fail_gate(self) -> None:
        path = self._write_json(
            "high_crit.json",
            _base_report(
                Results=[
                    {
                        "Target": "package-lock.json",
                        "Class": "lang-pkgs",
                        "Type": "npm",
                        "Vulnerabilities": [
                            {"VulnerabilityID": "CVE-1", "Severity": "CRITICAL"},
                            {"VulnerabilityID": "CVE-2", "Severity": "HIGH"},
                            {"VulnerabilityID": "CVE-3", "Severity": "LOW"},
                        ],
                    }
                ]
            ),
        )
        self.assertEqual(evaluate(path), 1)

    def test_medium_and_low_only_findings_pass_gate(self) -> None:
        path = self._write_json(
            "med_low.json",
            _base_report(
                Results=[
                    {
                        "Target": "package-lock.json",
                        "Class": "lang-pkgs",
                        "Type": "npm",
                        "Vulnerabilities": [
                            {"VulnerabilityID": "CVE-4", "Severity": "MEDIUM"},
                            {"VulnerabilityID": "CVE-5", "Severity": "LOW"},
                        ],
                    }
                ]
            ),
        )
        self.assertEqual(evaluate(path), 0)

    def test_clean_report_with_expected_target_passes_gate(self) -> None:
        path = self._write_json(
            "clean.json",
            _base_report(Results=[{
                "Target": "package-lock.json",
                "Class": "lang-pkgs",
                "Type": "npm",
            }]),
        )
        self.assertEqual(evaluate(path), 0)

    def test_missing_results_fails_closed(self) -> None:
        path = self._write_json("missing_results.json", _base_report())
        self.assertEqual(evaluate(path), 2)

    def test_empty_results_fails_closed(self) -> None:
        path = self._write_json("empty_results.json", _base_report(Results=[]))
        self.assertEqual(evaluate(path), 2)

    def test_unexpected_target_fails_closed(self) -> None:
        path = self._write_json(
            "wrong_target.json",
            _base_report(Results=[{
                "Target": "unrelated.lock",
                "Class": "lang-pkgs",
                "Type": "npm",
            }]),
        )
        self.assertEqual(evaluate(path), 2)

    def test_wrong_target_type_fails_closed(self) -> None:
        path = self._write_json(
            "wrong_type.json",
            _base_report(Results=[{
                "Target": "package-lock.json",
                "Class": "lang-pkgs",
                "Type": "pip",
            }]),
        )
        self.assertEqual(evaluate(path), 2)

    def test_empty_file_returns_scan_error(self) -> None:
        path = self.tmp_dir / "empty.json"
        path.write_text("", encoding="utf-8")
        self.assertEqual(evaluate(path), 2)

    def test_malformed_json_returns_scan_error(self) -> None:
        path = self.tmp_dir / "malformed.json"
        path.write_text("{not valid json", encoding="utf-8")
        self.assertEqual(evaluate(path), 2)

    def test_empty_object_without_trivy_metadata_returns_scan_error(self) -> None:
        path = self._write_json("empty_obj.json", {})
        self.assertEqual(evaluate(path), 2)

    def test_unexpected_json_structures_return_scan_error(self) -> None:
        cases = [
            ("array_root.json", []),
            ("results_null.json", _base_report(Results=None)),
            ("results_string.json", _base_report(Results="none")),
            ("result_not_dict.json", _base_report(Results=["bad", {"Target": "package-lock.json", "Class": "lang-pkgs", "Type": "npm"}])),
            (
                "vulns_not_list.json",
                _base_report(Results=[{"Target": "a", "Vulnerabilities": "bad"}]),
            ),
            (
                "vuln_not_dict.json",
                _base_report(Results=[{"Target": "a", "Vulnerabilities": ["CVE-1"]}]),
            ),
        ]
        for filename, payload in cases:
            with self.subTest(filename=filename):
                path = self._write_json(filename, payload)
                self.assertEqual(evaluate(path), 2)

    def test_missing_file_returns_scan_error(self) -> None:
        self.assertEqual(evaluate(self.tmp_dir / "does_not_exist.json"), 2)

    def test_directory_instead_of_file_returns_scan_error(self) -> None:
        self.assertEqual(evaluate(self.tmp_dir), 2)

    def test_cli_missing_argument_returns_scan_error(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(SCRIPT_PATH)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 2)


if __name__ == "__main__":
    unittest.main()
