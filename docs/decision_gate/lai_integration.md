# LAI → Decision Gate integration contract

The provider-neutral adapter in `src/reliability_adapter.py` bridges existing
belief observations to the operational request contract without assigning
permissions or changing LAI science.

Flow: `AgentBelief` → `ReliabilityObservation.from_agent_belief(...)` →
`to_decision_request(observation, **application_context)` → `DecisionRequest`.
The caller separately invokes `decision_gate.evaluate(request)`.

| Information | Translation |
| --- | --- |
| AgentBelief status and confidence | Copied unchanged into observation and request |
| Supporting/contradicting evidence | Detached copies retained in the observation |
| Explicit evidence conflict and persistence | Copied to request; absent values remain `None` |
| Timestamp and provenance | Retained when supplied; otherwise `None` |
| Action, context shift, quality, freshness, health, consequence, reversibility | Supplied separately by application context |
| Policy identifier/version | Existing gate defaults, or explicit caller values |

`AgentBelief` has no conflict flag, persistence, timestamp, or provenance fields.
The adapter does not manufacture them. It does not infer conflict from evidence
text or list presence, derive persistence from one belief, reinterpret LAI
`context_signal` as context shift, or infer freshness from timestamp metadata.
Persistence, when supplied, must use the existing gate's consecutive-observation
count convention. Only causally available information belongs in this interface;
hidden benchmark truth and retrospective evaluation metrics are not inputs.

Direct `ReliabilityObservation` construction supports partial information.
Missing evidence lists (`None`) remain distinct from observed empty lists (`()`).
The existing request has no evidence-list or metadata fields, so callers should
retain the observation alongside the request for review. Evidence and metadata
are copied, including nested values; they are not a persistent audit store.

Missing application signals remain `None`. Request validation and permission
policy remain the gate's responsibility: malformed signals are rejected there,
and missing required conflict/persistence or operational inputs block automatic
execution. Optional timestamp/provenance absence alone does not block. The
adapter does not silently correct invalid values or assign favorable defaults.

VALID is a belief status, not execution authorization. Confidence remains
certainty in that status, not probability of correctness. INVALID does not
establish operational impact. The same observation can yield GREEN for a
low-consequence reversible action and YELLOW for a high-consequence action with
low reversibility, under the existing gate policy and complete favorable inputs.

No providers, scientific definitions, evaluation metrics, experiments, or saved
artifacts are changed. There are no application scenarios, ranking rules, new
scientific measurements, or external calls in the adapter.
