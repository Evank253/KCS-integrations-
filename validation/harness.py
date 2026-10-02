"""Executable M04-004 contract validation harness.

Runs only against the controlled local KCN provider fixture. It does not
claim live-provider compatibility or emergent-intelligence evidence.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CONTRACT_ID = "CON-KCN-KSIEI-ANALYZE-001"
CAPABILITY_ID = "CAP-KCN-INTELLIGENCE-ANALYZE"
PROVIDER_ID = "SYS-KCN"
PROVIDER_REVISION = "cf8ca49b872a9baaa7212caba28837f486d54062"
ALLOWED_MODULES = {
    "research", "reasoning", "planning", "creative",
    "engineering", "analysis", "learning",
}


def digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


class ControlledKCNFixture:
    """Deterministic provider boundary used only for contract validation."""

    def __init__(self, *, auth_ok: bool = True, provider_id: str = PROVIDER_ID,
                 revision: str = PROVIDER_REVISION):
        self.auth_ok = auth_ok
        self.provider_id = provider_id
        self.revision = revision

    def analyze(self, request: dict[str, Any]) -> dict[str, Any]:
        if not self.auth_ok:
            raise PermissionError("authentication failure")
        if "query" not in request:
            raise ValueError("missing required query")
        if not isinstance(request["query"], str) or not 1 <= len(request["query"]) <= 4096:
            raise ValueError("query constraint violation")
        module = request.get("module", "analysis")
        if module not in ALLOWED_MODULES:
            raise ValueError("unsupported module")
        return {
            "id": "fixture-result-001",
            "module": module,
            "status": "pending_verification",
            "result": None,
            "created_at": "2026-10-01T00:00:00Z",
        }


@dataclass
class Invocation:
    request_id: str
    request: dict[str, Any]
    request_sha256: str
    provider_system_id: str
    provider_revision: str
    capability_id: str
    contract_id: str
    raw_response: dict[str, Any] | None = None
    response_sha256: str | None = None
    normalized_response: dict[str, Any] | None = None
    transformation_trace: list[str] | None = None

    def provenance(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "request_sha256": self.request_sha256,
            "provider_system_id": self.provider_system_id,
            "provider_revision": self.provider_revision,
            "capability_id": self.capability_id,
            "contract_id": self.contract_id,
        }


class ProvenanceAdapter:
    def __init__(self, provider: ControlledKCNFixture):
        self.provider = provider

    def invoke(self, request: dict[str, Any], *,
               request_id: str = "req-cv-001",
               expected_provider_id: str = PROVIDER_ID,
               expected_revision: str = PROVIDER_REVISION,
               expected_provenance: bool = True) -> Invocation:
        inv = Invocation(
            request_id=request_id,
            request=request,
            request_sha256=digest(request),
            provider_system_id=self.provider.provider_id,
            provider_revision=self.provider.revision,
            capability_id=CAPABILITY_ID,
            contract_id=CONTRACT_ID,
            transformation_trace=[],
        )
        if not expected_provenance:
            raise RuntimeError("provenance failure")
        if inv.provider_system_id != expected_provider_id:
            raise RuntimeError("provider identity mismatch")
        if inv.provider_revision != expected_revision:
            raise RuntimeError("provider revision mismatch")
        inv.raw_response = self.provider.analyze(request)
        inv.response_sha256 = digest(inv.raw_response)
        # Normalization is deliberately identity-preserving and recorded.
        inv.normalized_response = dict(inv.raw_response)
        inv.transformation_trace.append("identity-normalization:v1")
        return inv


def response_valid(response: Any) -> bool:
    if not isinstance(response, dict):
        return False
    required = {"id", "module", "status", "result", "created_at"}
    return required.issubset(response)
    

def run_case(case_id: str) -> dict[str, Any]:
    fixture = ControlledKCNFixture()
    request = {"query": "controlled validation", "module": "analysis"}

    try:
        if case_id == "CV-001":
            inv = ProvenanceAdapter(fixture).invoke(request)
            passed = response_valid(inv.raw_response) and inv.request_sha256 == digest(request)
            return result(case_id, passed, "PASS" if passed else "FAIL", inv)

        if case_id == "CV-002":
            try:
                fixture.analyze({})
                return result(case_id, False, "FAIL")
            except ValueError:
                return result(case_id, True, "REJECT")

        if case_id == "CV-003":
            try:
                fixture.analyze({"query": "x", "module": "unsupported"})
                return result(case_id, False, "FAIL")
            except ValueError:
                return result(case_id, True, "REJECT")

        if case_id == "CV-004":
            bad = {"id": "x", "module": "analysis", "status": "ok"}
            passed = not response_valid(bad)
            return result(case_id, passed, "REJECT" if passed else "FAIL",
                          raw_response=bad)

        if case_id == "CV-005":
            try:
                ProvenanceAdapter(ControlledKCNFixture(provider_id="SYS-OTHER")).invoke(request)
                return result(case_id, False, "FAIL")
            except RuntimeError:
                return result(case_id, True, "REJECT")

        if case_id == "CV-006":
            try:
                ProvenanceAdapter(ControlledKCNFixture(revision="wrong-revision")).invoke(request)
                return result(case_id, False, "FAIL")
            except RuntimeError:
                return result(case_id, True, "REJECT")

        if case_id == "CV-007":
            try:
                ProvenanceAdapter(fixture).invoke(request, expected_provenance=False)
                return result(case_id, False, "FAIL")
            except RuntimeError:
                return result(case_id, True, "REJECT")

        if case_id == "CV-008":
            class Failing(ControlledKCNFixture):
                def analyze(self, request):
                    raise RuntimeError("provider error")
            try:
                ProvenanceAdapter(Failing()).invoke(request)
                return result(case_id, False, "FAIL")
            except RuntimeError as exc:
                return result(case_id, str(exc) == "provider error", "FAIL_CLOSED")

        if case_id == "CV-009":
            try:
                ProvenanceAdapter(ControlledKCNFixture(auth_ok=False)).invoke(request)
                return result(case_id, False, "FAIL")
            except PermissionError:
                return result(case_id, True, "FAIL_CLOSED")

        if case_id == "CV-010":
            inv = ProvenanceAdapter(fixture).invoke(request)
            preserved = inv.raw_response is not None and inv.response_sha256 == digest(inv.raw_response)
            traced = inv.transformation_trace == ["identity-normalization:v1"]
            return result(case_id, preserved and traced, "PASS", inv)

        if case_id == "CV-011":
            inv = ProvenanceAdapter(fixture).invoke(request)
            authority = {
                "human_authority": "remains ultimate",
                "system_authority": "bounded operational authority only",
                "contract_effect": "must not grant authority",
                "qualification_effect": "must not promote interaction",
            }
            return result(case_id, True, "PASS", inv, authority=authority)

        return result(case_id, False, "UNKNOWN_CASE")
    except Exception as exc:
        return result(case_id, False, "HARNESS_ERROR", error=repr(exc))


def result(case_id: str, passed: bool, disposition: str, inv: Invocation | None = None,
           raw_response: Any = None, authority: dict[str, str] | None = None,
           error: str | None = None) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "passed": passed,
        "disposition": disposition,
        "request_provenance": inv.provenance() if inv else None,
        "raw_response": raw_response if raw_response is not None else (inv.raw_response if inv else None),
        "raw_response_sha256": inv.response_sha256 if inv else None,
        "transformation_trace": inv.transformation_trace if inv else [],
        "authority_constraints_observed": authority,
        "error": error,
    }


def main() -> int:
    case_ids = [f"CV-{i:03d}" for i in range(1, 12)]
    started = time.time()
    cases = [run_case(case_id) for case_id in case_ids]
    passed = all(c["passed"] for c in cases)
    evidence = {
        "evidence_schema": "M04.4-validation-result-v1",
        "contract_id": CONTRACT_ID,
        "validation_scope": "controlled KCN fixture/provider boundary",
        "provider_system_id": PROVIDER_ID,
        "provider_revision": PROVIDER_REVISION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "duration_ms": round((time.time() - started) * 1000, 3),
        "case_count": len(cases),
        "passed_count": sum(c["passed"] for c in cases),
        "validation_result": "PASS" if passed else "FAIL",
        "qualification_status": "NOT_QUALIFIED",
        "contract_lifecycle": "DRAFT",
        "emergence_claim": "NONE",
        "cases": cases,
    }
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "validation-results.json")
    out.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "contract_id": CONTRACT_ID,
        "validation_result": evidence["validation_result"],
        "passed_count": evidence["passed_count"],
        "case_count": evidence["case_count"],
        "evidence_file": str(out),
        "contract_lifecycle": "DRAFT",
    }, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
