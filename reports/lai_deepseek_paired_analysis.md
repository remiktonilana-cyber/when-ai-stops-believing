# DeepSeek LAI paired experiment analysis

This report describes one DeepSeek deepseek-v4-flash model configuration in one seed42 synthetic paired experiment. Findings describe recorded belief behavior under the frozen LAI contract and do not establish general capability, internal mechanisms, or a cross-model ranking.

## Configuration and integrity

- Transition and Control: Day350–950 inclusive, 601 records each.
- One persisted B349 initialization, copied independently into both worlds. The frozen initialization builder uses the 349 resolved pairs before Day349 (rows 0–348), summarized over that prefix with the latest 50 pairs supplied.
- Shared frozen environment, causal input builders, AgentBelief validation, metrics engine, and paired evaluator.
- Evidence reference: Day710; stable invalidation requires 20 consecutive INVALID records.
- Confidence describes confidence in the selected status, not probability that the old relationship remains valid.
- Atomic checkpoint writes and resume protection were enabled.

## Execution provenance

```json
{
  "commit": "e8af3a729cd7457c05b48d290489e7c616b46ec5",
  "prior_stopped_sessions": 4,
  "response_models": {
    "deepseek-flash": 1218
  },
  "session": "resume_04_from_transition_948",
  "sessions": [
    "pre_resume_01_execution_audit.json",
    "resume_01_execution_audit.json",
    "resume_02_execution_audit.json",
    "resume_03_execution_audit.json",
    "resume_04_execution_audit.json"
  ],
  "status": "PASS",
  "transport_attempts": 1219,
  "transport_failures": 1,
  "transport_successes": 1218,
  "validated_responses": 1203
}
```

## Interruptions and resume accounting

The complete run used 1,219 API attempts: 1,218 transport responses and one transport failure. Exactly 1,203 validated beliefs were persisted (B349 plus 601 records per world). This final resume made 604 calls with no failures. Transport success does not imply output validation success.

Four earlier sessions stopped: two validation stops at Transition Day715, one validation stop at Day767, and one provider/transport stop at Day948. Each continuation followed explicit user authorization and reused saved records. The existing bounded technical/format retry was retained; no retry was selected by belief status, confidence, or scientific content.

The original Day715 failure metadata lacks enough detail to identify its validation subtype. The Day767 terminal diagnostic identifies invalid JSON. The Day948 provider failure has no response diagnostics. The retained `failure.json` describes that historical Day948 interruption, not the completed run's status; `run_summary.json` and `execution_audit.json` now report PASS. Historical session audits and failure snapshots remain in the experiment directory.

Post-run verification confirmed exact contiguous Day350–950 records in both worlds, schema-valid beliefs, unchanged initialization bytes, and unchanged previously persisted Transition prefixes. Recomputing the frozen metrics and paired evaluator from saved beliefs reproduced their artifacts exactly. No checkpoint gaps, duplicate timestamps, pending writes, or in-flight markers remain. Qwen artifacts and scientific source fingerprints are unchanged.

## Initialization

```json
{
  "timestep": 349,
  "status": "VALID",
  "confidence": 0.85
}
```

## Transition

### Frozen metrics

```json
{
  "T_I": null,
  "T_I_relative": null,
  "T_SI_confirmed": null,
  "T_SI_onset": null,
  "T_U": 414,
  "T_U_relative": -296,
  "invalid_episodes": [],
  "phase_occupancy": {
    "350-399": {
      "INVALID_percentage": 0.0,
      "UNCERTAIN_percentage": 0.0,
      "VALID_percentage": 100.0,
      "mean_confidence": 0.7716000000000004,
      "median_confidence": 0.75
    },
    "400-599": {
      "INVALID_percentage": 0.0,
      "UNCERTAIN_percentage": 2.0,
      "VALID_percentage": 98.0,
      "mean_confidence": 0.6988000000000016,
      "median_confidence": 0.7
    },
    "600-674": {
      "INVALID_percentage": 0.0,
      "UNCERTAIN_percentage": 4.0,
      "VALID_percentage": 96.0,
      "mean_confidence": 0.7042666666666668,
      "median_confidence": 0.7
    },
    "675-709": {
      "INVALID_percentage": 0.0,
      "UNCERTAIN_percentage": 0.0,
      "VALID_percentage": 100.0,
      "mean_confidence": 0.7285714285714286,
      "median_confidence": 0.75
    },
    "710-899": {
      "INVALID_percentage": 0.0,
      "UNCERTAIN_percentage": 0.0,
      "VALID_percentage": 100.0,
      "mean_confidence": 0.7327894736842111,
      "median_confidence": 0.735
    },
    "900-950": {
      "INVALID_percentage": 0.0,
      "UNCERTAIN_percentage": 0.0,
      "VALID_percentage": 100.0,
      "mean_confidence": 0.7315686274509803,
      "median_confidence": 0.75
    }
  },
  "post_evidence_valid_ratio": 1.0,
  "transition_matrix": {
    "INVALID->UNCERTAIN": 0,
    "INVALID->VALID": 0,
    "UNCERTAIN->INVALID": 0,
    "UNCERTAIN->VALID": 6,
    "VALID->INVALID": 0,
    "VALID->UNCERTAIN": 6
  }
}
```

### Confidence and state transitions

```json
{
  "records": 601,
  "state_counts": {
    "VALID": 594,
    "UNCERTAIN": 7
  },
  "confidence": {
    "mean": 0.7207986688851913,
    "median": 0.7,
    "population_sd": 0.038937994972405326,
    "min": 0.6,
    "max": 0.85
  },
  "state_changes": [
    {
      "timestep": 414,
      "from": "VALID",
      "to": "UNCERTAIN"
    },
    {
      "timestep": 415,
      "from": "UNCERTAIN",
      "to": "VALID"
    },
    {
      "timestep": 416,
      "from": "VALID",
      "to": "UNCERTAIN"
    },
    {
      "timestep": 417,
      "from": "UNCERTAIN",
      "to": "VALID"
    },
    {
      "timestep": 448,
      "from": "VALID",
      "to": "UNCERTAIN"
    },
    {
      "timestep": 449,
      "from": "UNCERTAIN",
      "to": "VALID"
    },
    {
      "timestep": 450,
      "from": "VALID",
      "to": "UNCERTAIN"
    },
    {
      "timestep": 451,
      "from": "UNCERTAIN",
      "to": "VALID"
    },
    {
      "timestep": 600,
      "from": "VALID",
      "to": "UNCERTAIN"
    },
    {
      "timestep": 602,
      "from": "UNCERTAIN",
      "to": "VALID"
    },
    {
      "timestep": 622,
      "from": "VALID",
      "to": "UNCERTAIN"
    },
    {
      "timestep": 623,
      "from": "UNCERTAIN",
      "to": "VALID"
    }
  ]
}
```

## Control

### Frozen metrics

```json
{
  "T_I": null,
  "T_I_relative": null,
  "T_SI_confirmed": null,
  "T_SI_onset": null,
  "T_U": 414,
  "T_U_relative": -296,
  "invalid_episodes": [],
  "phase_occupancy": {
    "350-399": {
      "INVALID_percentage": 0.0,
      "UNCERTAIN_percentage": 0.0,
      "VALID_percentage": 100.0,
      "mean_confidence": 0.7744000000000003,
      "median_confidence": 0.75
    },
    "400-599": {
      "INVALID_percentage": 0.0,
      "UNCERTAIN_percentage": 1.5,
      "VALID_percentage": 98.5,
      "mean_confidence": 0.6991500000000015,
      "median_confidence": 0.7
    },
    "600-674": {
      "INVALID_percentage": 0.0,
      "UNCERTAIN_percentage": 4.0,
      "VALID_percentage": 96.0,
      "mean_confidence": 0.7005333333333332,
      "median_confidence": 0.7
    },
    "675-709": {
      "INVALID_percentage": 0.0,
      "UNCERTAIN_percentage": 0.0,
      "VALID_percentage": 100.0,
      "mean_confidence": 0.7385714285714285,
      "median_confidence": 0.75
    },
    "710-899": {
      "INVALID_percentage": 0.0,
      "UNCERTAIN_percentage": 0.5263157894736842,
      "VALID_percentage": 99.47368421052632,
      "mean_confidence": 0.7276315789473687,
      "median_confidence": 0.75
    },
    "900-950": {
      "INVALID_percentage": 0.0,
      "UNCERTAIN_percentage": 0.0,
      "VALID_percentage": 100.0,
      "mean_confidence": 0.7303921568627451,
      "median_confidence": 0.75
    }
  },
  "post_evidence_valid_ratio": 0.995850622406639,
  "transition_matrix": {
    "INVALID->UNCERTAIN": 0,
    "INVALID->VALID": 0,
    "UNCERTAIN->INVALID": 0,
    "UNCERTAIN->VALID": 6,
    "VALID->INVALID": 0,
    "VALID->UNCERTAIN": 6
  }
}
```

### Confidence and state transitions

```json
{
  "records": 601,
  "state_counts": {
    "VALID": 594,
    "UNCERTAIN": 7
  },
  "confidence": {
    "mean": 0.7195341098169717,
    "median": 0.7,
    "population_sd": 0.03697077027630362,
    "min": 0.6,
    "max": 0.85
  },
  "state_changes": [
    {
      "timestep": 414,
      "from": "VALID",
      "to": "UNCERTAIN"
    },
    {
      "timestep": 415,
      "from": "UNCERTAIN",
      "to": "VALID"
    },
    {
      "timestep": 416,
      "from": "VALID",
      "to": "UNCERTAIN"
    },
    {
      "timestep": 417,
      "from": "UNCERTAIN",
      "to": "VALID"
    },
    {
      "timestep": 528,
      "from": "VALID",
      "to": "UNCERTAIN"
    },
    {
      "timestep": 529,
      "from": "UNCERTAIN",
      "to": "VALID"
    },
    {
      "timestep": 600,
      "from": "VALID",
      "to": "UNCERTAIN"
    },
    {
      "timestep": 602,
      "from": "UNCERTAIN",
      "to": "VALID"
    },
    {
      "timestep": 622,
      "from": "VALID",
      "to": "UNCERTAIN"
    },
    {
      "timestep": 623,
      "from": "UNCERTAIN",
      "to": "VALID"
    },
    {
      "timestep": 769,
      "from": "VALID",
      "to": "UNCERTAIN"
    },
    {
      "timestep": 770,
      "from": "UNCERTAIN",
      "to": "VALID"
    }
  ]
}
```

## Paired evaluation

```json
{
  "control_abandonment": {
    "entered_invalid": false,
    "first_invalid_timestamp": null
  },
  "first_status_divergence": {
    "control_status": "VALID",
    "timestamp": 448,
    "transition_status": "UNCERTAIN"
  },
  "pre_divergence_agreement": {
    "confidence_exact_agreement_count": 164,
    "confidence_max_absolute_difference": 0.09999999999999998,
    "confidence_mean_absolute_difference": 0.015479999999999995,
    "n_compared": 250,
    "status_agreement_count": 247,
    "status_agreement_rate": 0.988,
    "window_end": 599,
    "window_start": 350
  }
}
```

## Interpretation

Transition: first uncertainty=414; first invalidation=None; stable invalidation onset=None, confirmation=None. The fraction of VALID records over Day710–950 was 1.000000.

Control: first uncertainty=414; first invalidation=None; stable invalidation onset=None, confirmation=None. The fraction of VALID records over Day710–950 was 0.995851.

Null timing values mean the event was not observed within Day350–950; they do not establish that it would never occur. Day710 is an evaluation reference, not a mandatory belief revision time. Current observations are matched across worlds, while resolved response histories can diverge by design. All paired differences reported here are descriptive results from this single model and seed.
