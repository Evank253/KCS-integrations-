# Contract Validation — M04-004

Validation establishes compatibility; it does not activate a contract.

For each contract validate:
- canonical system and capability identifiers
- provider revision
- request schema
- response schema
- transport
- authentication boundary
- provenance propagation
- transformation trace
- failure behavior
- authority constraints

A successful validation may transition DRAFT → VALIDATED only when all required checks have evidence.
