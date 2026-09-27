# Developer Contract

## What Decision Gate does

Decision Gate evaluates whether a proposed action is permitted under supplied
information using deterministic prototype policy. It does not predict outcomes,
generate reliability signals, or execute actions.

## Conceptual flow

```text
AI system
    |
    v
Application constructs DecisionRequest
    |
    v
evaluate()
    |
    v
GateDecision
    |
    v
Application decides execution
```

## Minimal example

Follow [lightweight installation](setup.md#lightweight-decision-gate-usage), then
run this example from your own Python project. These are illustrative supplied
values, not measurements inferred by the Gate.

```python
from when_ai_stops_believing import DecisionRequest, evaluate

request = DecisionRequest(
    action_id="draft-1",
    proposed_action="Update a reversible draft",
    belief_status="VALID",
    confidence=0.8,
    evidence_conflict=False,
    belief_persistence=3,
    context_shift=False,
    data_quality="GOOD",
    data_freshness="FRESH",
    system_health="HEALTHY",
    consequence_level="LOW",
    reversibility="HIGH",
)

decision = evaluate(request)
print(decision.permission, decision.reason_codes)
```

Expected output:

```text
GREEN ('POLICY_REQUIREMENTS_MET',)
```

The application must separately enforce permission for the evaluated action.

## Input ownership

| Supplied by | Fields |
| --- | --- |
| AI/system integration | `belief_status`, `confidence`, `evidence_conflict`, `belief_persistence` |
| Environment/operations integration | `context_shift`, `data_quality`, `data_freshness`, `system_health` |
| Application policy | `consequence_level`, `reversibility` |

The application also supplies nonempty `action_id` and `proposed_action` strings.
Policy defaults are `minimum-universal-gate`, version `1`.

The Gate does not infer missing information. Although signal fields default to
`None` in the constructor, every signal is required to avoid a missing-information
RED. Unknown values must stay `None`, not become favorable defaults. Unsupported
policy identifiers or versions also produce RED.

Malformed values raise `ValueError`; passing an object other than a
`DecisionRequest` raises `TypeError`. Validation failure provides no permission
to execute. See the [policy contract](decision_gate_prototype.md) and
[request definition](../src/decision_gate.py) for accepted values.

Confidence and belief persistence are validated and required but have no
permission thresholds. Persistence counts consecutive observations retaining the
current belief status. Freshness is classified upstream against application
requirements; the Gate does not calculate data age.

## Permission semantics

| Permission | Application meaning |
| --- | --- |
| GREEN | Permission under prototype policy; the application controls execution. |
| YELLOW | Hold for human review; the package contains no approval workflow. |
| RED | Block/hold; ordinary confirmation does not bypass the block. |

RED overrides YELLOW. Missing information, stale/unusable data, an unhealthy
system, or an INVALID belief block permission. Context shift, evidence conflict,
an UNCERTAIN belief, degraded data, high consequence, or low reversibility require
review when no blocking condition applies.

**VALID does not automatically imply GREEN. Confidence is not probability of
success.** It describes certainty in the supplied belief status.

## Output contract

`GateDecision` contains:

- `permission`: `GREEN`, `YELLOW`, or `RED`.
- `reason_codes`: machine-readable reasons; GREEN reports `POLICY_REQUIREMENTS_MET`.
- `assessment`: `missing_fields`, `blocking_reasons`, and `review_reasons`.
- `requires_human_review`: true only for YELLOW; false does not imply permission.
- `action_id` and `proposed_action`: the evaluated action.
- `policy_id` and `policy_version`: the policy actually applied.

Package version `1.1.0` is separate from policy version `1`. Results are immutable
assessment snapshots, not durable authorization tokens. Applications own
execution enforcement, reassessment when conditions change, and review records.

## Adapter relationship

The optional `when_ai_stops_believing.reliability` interface exports
`AgentBelief`, `BeliefStatus`, `ReliabilityObservation`, and
`to_decision_request`. Direct Gate use does not require the adapter.

The Reliability Adapter translates supplied information. It does not detect
reliability, infer context shift, infer conflict, or decide permission.
Application context is supplied separately. Evidence and provenance remain in
the observation rather than the request; retain the observation when needed for
review. See the [adapter integration contract](decision_gate/lai_integration.md).

## Limitations

This package has no executor, audit service, or production authorization system.
Its deterministic policy does not output a calibrated safety probability.
Signal producers, approval workflows, authorization expiry, and replay prevention
remain application responsibilities or future integrations.
