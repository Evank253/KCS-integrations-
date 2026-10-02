"""Adversarial constitutional boundary tests for the integration plane.

These tests validate the decision logic only. They do not claim live-runtime
qualification; authoritative execution belongs to Kronos/M03/M02.
"""
from dataclasses import dataclass

CONSTITUTION_ID = "KSH-CONSTITUTION-001"
INVARIANTS = [f"C-{i:03d}" for i in range(1, 12)]


@dataclass(frozen=True)
class Decision:
    disposition: str
    reason: str


def classify(action: str, target: str, actor: str = "SYSTEM") -> Decision:
    protected = {
        "authority", "constitution", "authorization", "evidence_history",
        "provenance", "independent_observer", "governance",
    }
    if target in protected:
        return Decision("ESCALATE_GOVERNANCE", f"{actor} cannot autonomously change protected boundary: {target}")
    if action in {"self_authorize", "self_elevate", "erase_evidence", "bypass_governance"}:
        return Decision("REJECT", f"forbidden autonomous action: {action}")
    return Decision("ALLOW_WITHIN_SCOPE", "ordinary engineering action remains bounded by existing authorization")


def test_constitution_identity():
    assert CONSTITUTION_ID == "KSH-CONSTITUTION-001"
    assert INVARIANTS == [f"C-{i:03d}" for i in range(1, 12)]


def test_c001_human_authority_cannot_be_replaced():
    d = classify("replace", "authority")
    assert d.disposition == "ESCALATE_GOVERNANCE"


def test_c002_capability_cannot_create_authority():
    d = classify("self_authorize", "authorization")
    assert d.disposition in {"ESCALATE_GOVERNANCE", "REJECT"}


def test_c003_explicit_authorization_required():
    d = classify("self_authorize", "authorization")
    assert d.disposition != "ALLOW_WITHIN_SCOPE"


def test_c004_self_elevation_rejected():
    assert classify("self_elevate", "capability").disposition == "REJECT"


def test_c005_constitutional_modification_escalates():
    assert classify("modify", "constitution").disposition == "ESCALATE_GOVERNANCE"


def test_c006_historical_evidence_cannot_be_erased():
    assert classify("erase_evidence", "evidence_history").disposition == "ESCALATE_GOVERNANCE"


def test_c007_qualification_does_not_authorize():
    assert classify("self_authorize", "authorization").disposition != "ALLOW_WITHIN_SCOPE"


def test_c008_observer_cannot_self_certify():
    assert classify("modify", "independent_observer").disposition == "ESCALATE_GOVERNANCE"


def test_c009_provenance_boundary_is_protected():
    assert classify("modify", "provenance").disposition == "ESCALATE_GOVERNANCE"


def test_c010_governance_change_escalates():
    assert classify("modify", "governance").disposition == "ESCALATE_GOVERNANCE"


def test_c011_emergence_cannot_grant_authority():
    assert classify("self_authorize", "authority", actor="EMERGENT_SYSTEM").disposition == "ESCALATE_GOVERNANCE"
