<!--
Crisis response for production system failures.
Use when production shows signs of failure or during emergencies.
-->

Invoke the production-incident-responder skill for incident response.

## Arguments

- `$ARGUMENTS` - Symptom description or alert message

## Response Protocol

1. Assess severity (P1-P4)
2. Identify affected systems
3. Check health endpoints
4. Review recent changes
5. Propose mitigation
6. Document incident

## Severity Levels

- P1: Complete outage, all users affected
- P2: Major functionality broken
- P3: Minor functionality degraded
- P4: Cosmetic or low-impact issue
