# Urban Traffic Decision Gate Demo

Synthetic Decision Gate demonstration — no live traffic control.

From the repository root:

```sh
python -m applications.urban_traffic.run_demo --output-dir /tmp/urban-traffic-demo
```

Open the generated `index.html`; `demo_results.json` contains the complete records.
Use a dedicated output directory separate from scientific results. Runs overwrite
these two demo files. All inputs are local deterministic fixtures; no API or
model is used. The HTML needs no network connection.

Flow: synthetic environment → scripted proposal → application adapter → existing
reliability adapter → unchanged Decision Gate → simulated execution.

Exactly three independent scenarios share VALID belief, confidence 0.8, explicit
no evidence conflict, and persistence 3. Normal operation yields GREEN/EXECUTED;
an explicit context shift yields YELLOW/HELD; unhealthy controller yields
RED/BLOCKED. YELLOW has no approval bypass and RED has no override.

The only permitted action changes NS green configuration from 30 to 35 synthetic
seconds for the next cycle. EW remains 30. Queues are displayed observations,
not a movement simulation. The timing values and LOW consequence/HIGH reversibility
classification are demo conventions, not traffic engineering recommendations.
The simulator rejects out-of-scope actions before mutation and tracks action IDs
to prevent duplicate execution within the state instance.

The adapter copies belief information and supplies application context. Complete
nonnegative integer queues map to GOOD quality; absent queues remain unknown;
invalid queues map to UNUSABLE. Equal observation/decision steps mean FRESH;
older observations mean STALE; missing timestamps remain unknown. Invalid or
future observation timestamps are unusable. Conflict and context shift are
explicit signals, not inferred from evidence text. Gate validation errors and
action-scope mismatches abort without mutation.

The report shows situation, state, scripted proposal, belief, confidence,
permission, reason codes, review requirement, and before/after execution state.
It demonstrates integration and authorization enforcement, not traffic gains,
real-city readiness, certification, new LAI science, or production security.

Tests: `python -m pytest -q tests/test_urban_traffic_demo.py`.
