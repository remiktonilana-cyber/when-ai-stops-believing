# E7.1 minimum Decision Gate

`src/decision_gate.py` implements the E7.0 request → validation → assessment →
permission flow as a pure, provider-neutral function: `evaluate(DecisionRequest)`.
It uses the existing LAI belief-status vocabulary without changing LAI behavior.

All signal fields are mandatory for automatic permission. `None` explicitly
represents unavailable information and produces RED, with the missing field names
in the assessment. Malformed values raise `ValueError` (wrong request types raise
`TypeError`); callers must not execute on validation failure.

Policy `minimum-universal-gate`, version `1`, applies these rules:

| Condition | Result |
| --- | --- |
| Missing signal or policy metadata; unsupported policy | RED |
| Stale data, unusable data, unhealthy system, INVALID belief | RED |
| UNCERTAIN belief, evidence conflict, context shift, degraded data | YELLOW |
| High consequence or low reversibility | YELLOW |
| Complete valid inputs and none of the above | GREEN |

RED overrides YELLOW. Every matching rule retains its reason code. Only YELLOW
sets `requires_human_review` and adds `HUMAN_REVIEW_REQUIRED`; RED requires
remediation and reassessment, not ordinary confirmation. GREEN reports
`POLICY_REQUIREMENTS_MET`.

Confidence is certainty in the stated belief status, not action-success
probability. Confidence and belief persistence are validated and required but
have no permission thresholds. Persistence is a descriptive count of consecutive
observations with the current status, including zero when no prior persistence is
established. The gate does not compute a new scientific measure from that count.

The caller supplies conflict, context shift, quality, freshness, health, and
impact classifications from available evidence and application policy. Unknown
values must remain `None`. Freshness has no universal time threshold here; the
application must assess it at the decision time. The binary impact vocabulary
is deliberately limited to LOW/HIGH for this prototype.

Results bind to both `action_id` and `proposed_action` and identify the policy
actually applied. Structured assessment separates missing fields, blocking
reasons, and review reasons. There is no approval argument or execution method.
YELLOW holds execution pending a future review integration. These immutable
records are assessment snapshots, not tamper-proof authorization tokens.

Execution enforcement, authorization expiry, human identity/approval workflows,
signal producers, and persistent audit storage remain future integrations. No
provider modules, scientific evaluators, experiments, or saved artifacts are
modified by this core. No weighted score, calibrated probability, or claim of
real-world effectiveness is introduced.

Run focused tests with:

```sh
python -m unittest discover -s tests -p test_decision_gate.py -v
```
