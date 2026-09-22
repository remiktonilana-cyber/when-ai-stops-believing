# Qwen LAI Paired Scientific Analysis

This report describes observable belief-revision behavior from Qwen/qwen-plus in one canonical seed42 synthetic matched-pair experiment over Days 350–950. It is not a model ranking or a general capability claim. `T_evidence=710` is a benchmark reference, not a uniquely correct revision time.

## Frozen experiment and integrity

- Initialization: exactly one persisted B349_init, detached for both worlds.
- Transition and Control are matched canonical worlds; no successful timestep was regenerated.
- Scientific responses: 1 initialization + 601 Transition + 601 Control = 1203.
- The Agent received only causal contract fields; hidden/future leakage audit passed.

## Transition metrics

```json
{
  "T_I": 448,
  "T_I_relative": -262,
  "T_I_relative_to_710": -262,
  "T_I_right_censored": false,
  "T_SI_confirmed": null,
  "T_SI_confirmed_relative_to_710": null,
  "T_SI_confirmed_right_censored": true,
  "T_SI_onset": null,
  "T_SI_onset_relative_to_710": null,
  "T_SI_onset_right_censored": true,
  "T_U": null,
  "T_U_relative": null,
  "T_U_relative_to_710": null,
  "T_U_right_censored": true,
  "confidence_stats_350-399": {
    "max": 0.999,
    "mean": 0.99504,
    "median": 0.998,
    "min": 0.96,
    "sd": 0.007304683429143258
  },
  "confidence_stats_400-599": {
    "max": 0.999,
    "mean": 0.97993,
    "median": 0.98,
    "min": 0.92,
    "sd": 0.013647897273939318
  },
  "confidence_stats_600-674": {
    "max": 0.999,
    "mean": 0.9866933333333333,
    "median": 0.99,
    "min": 0.95,
    "sd": 0.011773386183346848
  },
  "confidence_stats_675-709": {
    "max": 0.997,
    "mean": 0.9864571428571428,
    "median": 0.99,
    "min": 0.96,
    "sd": 0.0091537435188104
  },
  "confidence_stats_710-899": {
    "max": 0.999,
    "mean": 0.9735105263157895,
    "median": 0.97,
    "min": 0.94,
    "sd": 0.013993509575846505
  },
  "confidence_stats_900-950": {
    "max": 0.98,
    "mean": 0.9698039215686274,
    "median": 0.97,
    "min": 0.95,
    "sd": 0.007538189328133766
  },
  "invalid_episodes": [
    {
      "end": 448,
      "length": 1,
      "start": 448
    }
  ],
  "phase_occupancy": {
    "350-399": {
      "INVALID_percentage": 0.0,
      "UNCERTAIN_percentage": 0.0,
      "VALID_percentage": 100.0,
      "mean_confidence": 0.9950400000000009,
      "median_confidence": 0.998
    },
    "400-599": {
      "INVALID_percentage": 0.5,
      "UNCERTAIN_percentage": 0.0,
      "VALID_percentage": 99.5,
      "mean_confidence": 0.9799300000000025,
      "median_confidence": 0.98
    },
    "600-674": {
      "INVALID_percentage": 0.0,
      "UNCERTAIN_percentage": 0.0,
      "VALID_percentage": 100.0,
      "mean_confidence": 0.9866933333333336,
      "median_confidence": 0.99
    },
    "675-709": {
      "INVALID_percentage": 0.0,
      "UNCERTAIN_percentage": 0.0,
      "VALID_percentage": 100.0,
      "mean_confidence": 0.9864571428571427,
      "median_confidence": 0.99
    },
    "710-899": {
      "INVALID_percentage": 0.0,
      "UNCERTAIN_percentage": 0.0,
      "VALID_percentage": 100.0,
      "mean_confidence": 0.9735105263157895,
      "median_confidence": 0.97
    },
    "900-950": {
      "INVALID_percentage": 0.0,
      "UNCERTAIN_percentage": 0.0,
      "VALID_percentage": 100.0,
      "mean_confidence": 0.9698039215686264,
      "median_confidence": 0.97
    }
  },
  "post_evidence_I_to_U": 0,
  "post_evidence_I_to_V": 0,
  "post_evidence_state_changes": 0,
  "post_evidence_valid_count": 241,
  "post_evidence_valid_rate": 1.0,
  "post_evidence_valid_ratio": 1.0,
  "post_evidence_window_count": 241,
  "state_counts": {
    "INVALID": 1,
    "UNCERTAIN": 0,
    "VALID": 600
  },
  "state_occupancy_percent": {
    "INVALID": 0.16638935108153077,
    "UNCERTAIN": 0.0,
    "VALID": 99.83361064891847
  },
  "total_state_changes": 2,
  "transition_matrix": {
    "INVALID->UNCERTAIN": 0,
    "INVALID->VALID": 1,
    "UNCERTAIN->INVALID": 0,
    "UNCERTAIN->VALID": 0,
    "VALID->INVALID": 1,
    "VALID->UNCERTAIN": 0
  }
}
```

## Control metrics

```json
{
  "T_I": 401,
  "T_I_relative": -309,
  "T_I_relative_to_710": -309,
  "T_I_right_censored": false,
  "T_SI_confirmed": null,
  "T_SI_confirmed_relative_to_710": null,
  "T_SI_confirmed_right_censored": true,
  "T_SI_onset": null,
  "T_SI_onset_relative_to_710": null,
  "T_SI_onset_right_censored": true,
  "T_U": 448,
  "T_U_relative": -262,
  "T_U_relative_to_710": -262,
  "T_U_right_censored": false,
  "confidence_stats_350-399": {
    "max": 0.99,
    "mean": 0.9884,
    "median": 0.99,
    "min": 0.96,
    "sd": 0.00542586398650022
  },
  "confidence_stats_400-599": {
    "max": 0.995,
    "mean": 0.978575,
    "median": 0.98,
    "min": 0.82,
    "sd": 0.017807143931579825
  },
  "confidence_stats_600-674": {
    "max": 0.99,
    "mean": 0.9769333333333333,
    "median": 0.99,
    "min": 0.72,
    "sd": 0.03592485985436207
  },
  "confidence_stats_675-709": {
    "max": 0.998,
    "mean": 0.9787714285714285,
    "median": 0.99,
    "min": 0.82,
    "sd": 0.03225176470413073
  },
  "confidence_stats_710-899": {
    "max": 0.999,
    "mean": 0.9874368421052632,
    "median": 0.99,
    "min": 0.82,
    "sd": 0.01884713326033867
  },
  "confidence_stats_900-950": {
    "max": 0.99,
    "mean": 0.9804901960784314,
    "median": 0.98,
    "min": 0.97,
    "sd": 0.007157534215076077
  },
  "invalid_episodes": [
    {
      "end": 401,
      "length": 1,
      "start": 401
    },
    {
      "end": 416,
      "length": 1,
      "start": 416
    },
    {
      "end": 806,
      "length": 1,
      "start": 806
    }
  ],
  "phase_occupancy": {
    "350-399": {
      "INVALID_percentage": 0.0,
      "UNCERTAIN_percentage": 0.0,
      "VALID_percentage": 100.0,
      "mean_confidence": 0.9884000000000002,
      "median_confidence": 0.99
    },
    "400-599": {
      "INVALID_percentage": 1.0,
      "UNCERTAIN_percentage": 0.5,
      "VALID_percentage": 98.5,
      "mean_confidence": 0.978575000000003,
      "median_confidence": 0.98
    },
    "600-674": {
      "INVALID_percentage": 0.0,
      "UNCERTAIN_percentage": 1.3333333333333333,
      "VALID_percentage": 98.66666666666667,
      "mean_confidence": 0.9769333333333337,
      "median_confidence": 0.99
    },
    "675-709": {
      "INVALID_percentage": 0.0,
      "UNCERTAIN_percentage": 2.857142857142857,
      "VALID_percentage": 97.14285714285714,
      "mean_confidence": 0.9787714285714283,
      "median_confidence": 0.99
    },
    "710-899": {
      "INVALID_percentage": 0.5263157894736842,
      "UNCERTAIN_percentage": 0.5263157894736842,
      "VALID_percentage": 98.94736842105263,
      "mean_confidence": 0.9874368421052633,
      "median_confidence": 0.99
    },
    "900-950": {
      "INVALID_percentage": 0.0,
      "UNCERTAIN_percentage": 0.0,
      "VALID_percentage": 100.0,
      "mean_confidence": 0.9804901960784318,
      "median_confidence": 0.98
    }
  },
  "post_evidence_I_to_U": 0,
  "post_evidence_I_to_V": 1,
  "post_evidence_state_changes": 4,
  "post_evidence_valid_count": 239,
  "post_evidence_valid_rate": 0.991701244813278,
  "post_evidence_valid_ratio": 0.991701244813278,
  "post_evidence_window_count": 241,
  "state_counts": {
    "INVALID": 3,
    "UNCERTAIN": 4,
    "VALID": 594
  },
  "state_occupancy_percent": {
    "INVALID": 0.49916805324459235,
    "UNCERTAIN": 0.6655574043261231,
    "VALID": 98.83527454242929
  },
  "total_state_changes": 14,
  "transition_matrix": {
    "INVALID->UNCERTAIN": 0,
    "INVALID->VALID": 3,
    "UNCERTAIN->INVALID": 0,
    "UNCERTAIN->VALID": 4,
    "VALID->INVALID": 3,
    "VALID->UNCERTAIN": 4
  }
}
```

## Paired metrics

```json
{
  "causal_input_match_350_599": true,
  "causal_input_mismatch_timesteps": [],
  "confidence_difference_summary_350_599": {
    "max": 0.16000000000000003,
    "mean_absolute": 0.01217200000000001,
    "median_absolute": 0.010000000000000009,
    "min": 0.0,
    "n": 250,
    "sd": 0.015833837690212696
  },
  "control_abandonment": {
    "entered_invalid": true,
    "first_invalid_timestamp": 401
  },
  "first_status_divergence": {
    "control_status": "INVALID",
    "timestamp": 401,
    "transition_status": "VALID"
  },
  "pre_divergence_agreement": {
    "confidence_exact_agreement_count": 75,
    "confidence_max_absolute_difference": 0.16000000000000003,
    "confidence_mean_absolute_difference": 0.012171999999999994,
    "n_compared": 250,
    "status_agreement_count": 247,
    "status_agreement_rate": 0.988,
    "window_end": 599,
    "window_start": 350
  }
}
```

## Interpretation boundaries

Observation: these are the recorded Qwen belief states, confidence values, and frozen-window summaries under the contract.

Behavioral pattern under this benchmark: differences between Transition and Control are descriptive paired observations from this one synthetic seed and model configuration.

Paired benchmark interpretation: the matched design isolates observable belief-revision behavior when the response law differs, while T_evidence remains a model-independent reference rather than a mandatory decision time. This experiment does not identify internal model mechanisms, establish general intelligence, or support cross-model ranking.

## Interpretation audit

In the Transition trajectory, the first INVALID at Day448 is an isolated pre-structural INVALID excursion: it occurs before `T_structural=600`, lasts one timestep, and returns immediately to VALID. It is not described as successful structural adaptation, transition detection, or evidence-driven invalidation. No stable INVALID episode occurred. The all-VALID Day710–950 record is described as persistent VALID belief after the benchmark evidence reference, or Persistent Outdated Belief under this canonical benchmark run.

The Control trajectory has no structural amplification transition. Its transient INVALID and UNCERTAIN states are reported descriptively and are not treated as correct transition detection. The greater number of Control state changes is likewise descriptive; no internal cause is inferred.

For Days350–599, Agent-visible causal inputs matched while some outputs differed. This is reported as output variation under identical Agent-visible inputs, cautiously consistent with provider/model stochasticity; no specific internal mechanism is claimed.

All missing timing events remain explicit `null` right-censored values. No censored event was converted to Day951, and absence within this horizon is not evidence that the event could never occur outside it.

## Technical provenance and causal audit

Technical failures are separate from scientific responses: Day409 had two malformed structured-output attempts; network/transport failures occurred at Days659, 830, 917, 634, 669, 697, 730, 773, 844, and 896 before accepted responses. These did not create AgentBelief records. All 1,203 accepted scientific responses are unique and contiguous. The causal audit found no current unresolved response, previous explanation, hidden benchmark field, or future observation in Agent-visible inputs; resolved history never exceeded 50 pairs.

The Transition and Control worlds shared the same detached B349 initialization. This is one Qwen/qwen-plus run on one canonical synthetic seed42 matched-pair experiment over Days350–950. The results describe observable belief-revision behavior under this contract only; they do not identify an internal model mechanism or establish general capability, intelligence, or a cross-model ranking.
