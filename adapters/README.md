# Provenance-Preserving Adapters

Adapters normalize system interfaces without erasing provider identity or source provenance.

Required flow:

REQUEST
→ immutable request record
→ provider invocation
→ raw response preservation
→ schema validation
→ optional normalization
→ transformation record
→ consumer response

An adapter must never synthesize a provider result, suppress a provider failure, or convert an unverified interaction into intelligence evidence.
