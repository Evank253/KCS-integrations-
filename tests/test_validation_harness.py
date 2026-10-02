import json
import tempfile
import unittest
from pathlib import Path

from validation.harness import main, run_case


class ContractValidationHarnessTests(unittest.TestCase):
    def test_all_cases_pass_against_controlled_fixture(self):
        cases = [run_case(f"CV-{i:03d}") for i in range(1, 12)]
        self.assertTrue(all(case["passed"] for case in cases), cases)

    def test_machine_readable_evidence_is_generated(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "validation-results.json"
            import sys
            original = sys.argv[:]
            try:
                sys.argv = ["harness", str(target)]
                self.assertEqual(main(), 0)
            finally:
                sys.argv = original
            evidence = json.loads(target.read_text(encoding="utf-8"))
            self.assertEqual(evidence["validation_result"], "PASS")
            self.assertEqual(evidence["case_count"], 11)
            self.assertEqual(evidence["passed_count"], 11)
            self.assertEqual(evidence["contract_lifecycle"], "DRAFT")
            self.assertEqual(evidence["qualification_status"], "NOT_QUALIFIED")
            self.assertEqual(evidence["emergence_claim"], "NONE")

    def test_provenance_contains_contract_and_provider_revision(self):
        result = run_case("CV-001")
        provenance = result["request_provenance"]
        self.assertEqual(provenance["contract_id"], "CON-KCN-KSIEI-ANALYZE-001")
        self.assertEqual(provenance["provider_system_id"], "SYS-KCN")
        self.assertEqual(len(provenance["provider_revision"]), 40)

    def test_raw_response_precedes_normalization_trace(self):
        result = run_case("CV-010")
        self.assertIsNotNone(result["raw_response"])
        self.assertEqual(result["transformation_trace"], ["identity-normalization:v1"])

    def test_failure_cases_fail_closed(self):
        self.assertEqual(run_case("CV-008")["disposition"], "FAIL_CLOSED")
        self.assertEqual(run_case("CV-009")["disposition"], "FAIL_CLOSED")


if __name__ == "__main__":
    unittest.main()
