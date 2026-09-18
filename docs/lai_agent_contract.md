# LAI Agent information contract

This contract defines the information boundary for a future LAI Agent
evaluation. It is an interface specification, not an Agent implementation.
The Agent receives only causally available information at the current
timestep; hidden benchmark truth and future outcomes remain outside the
interface.

## Agent-visible information

The current observation contains:

- `fragility`
- `crowding`
- `liquidity_stress`
- `context_signal`
- `current_shock`

The previous belief contains:

- `belief_status`
- `confidence`
- `evidence_summary`

Resolved history contains the latest resolved `(shock, response)` pairs, in
causal order. At most 50 pairs are supplied. A response is included only after
the corresponding shock-response pair has resolved.

The historical summary contains:

- `resolved_count`
- `lifetime_shock_response_slope`
- `lifetime_residual_rmse`

`context_signal` is an Agent-visible context feature defined by the future
observation adapter; this document does not assign it hidden-state semantics.

## Forbidden information

The Agent must not receive or derive its belief directly from:

- `latent_stress`
- `latent_state`
- `alpha`
- `phase`
- `T_warning`
- `T_structural`
- `T_delta`
- `T_evidence`
- `future_response`
- `future_observations`

These fields are benchmark ground truth, future information, or audit-only
quantities. In particular, `T_evidence` is a model-independent reference for
later evaluation and is not an Agent input.

## Belief output

The schema-only representation in `src/lai_agent_schema.py` uses the statuses
`VALID`, `UNCERTAIN`, and `INVALID`, a confidence in `[0, 1]`, an explanation,
and a bounded supporting/contradicting evidence summary. This module performs
validation only; it does not choose a status, revise a belief, or call a model.
