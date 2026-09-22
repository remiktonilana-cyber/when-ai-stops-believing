import json

import pytest

from src.qwen_provider import LAI_AGENT_BELIEF_JSON_SCHEMA, QwenProvider
from src.universal_llm_adapter import validate_model_output
from src.lai_qwen_paired_experiment import run_paired_experiment
from src.lai_transition_environment import generate_transition
from src.lai_transition_reference import D_PLUS


def valid():
    return {
        "belief_status": "VALID", "confidence": .5, "explanation": "brief",
        "evidence_summary": {"supporting_evidence": [], "contradicting_evidence": []},
    }


def test_exact_schema_is_accepted():
    assert validate_model_output(valid()) is True
    assert LAI_AGENT_BELIEF_JSON_SCHEMA["additionalProperties"] is False


@pytest.mark.parametrize("summary", [
    {"supporting_evidence": [], "contradicting": []},
    {"supporting_evidence": [], "contradicting_evidence": [], "extra": []},
])
def test_wrong_missing_or_extra_evidence_keys_rejected(summary):
    output = valid(); output["evidence_summary"] = summary
    with pytest.raises(ValueError, match="Malformed evidence_summary fields"):
        validate_model_output(output)


def test_evidence_limits_and_item_types_rejected():
    for field in ("supporting_evidence", "contradicting_evidence"):
        output = valid(); output["evidence_summary"][field] = ["x"] * 4
        with pytest.raises(ValueError, match="more than 3"):
            validate_model_output(output)
        output = valid(); output["evidence_summary"][field] = [7]
        with pytest.raises(ValueError, match="items must be strings"):
            validate_model_output(output)


def test_status_and_confidence_rejected():
    output = valid(); output["belief_status"] = "MAYBE"
    with pytest.raises(ValueError): validate_model_output(output)
    for value in (-.01, 1.01):
        output = valid(); output["confidence"] = value
        with pytest.raises(ValueError): validate_model_output(output)


def test_lai_provider_uses_exact_machine_schema_and_safe_diagnostics():
    malformed = valid()
    malformed["evidence_summary"] = {"supporting": ["secret text"], "contradicting_evidence": []}
    payloads = []

    def transport(payload, api_key, timeout):
        payloads.append(payload)
        return {"model": "qwen-plus", "choices": [{"finish_reason": "stop",
                "message": {"content": json.dumps(malformed)}}]}

    provider = QwenProvider(api_key="test-key-not-real", transport=transport,
                            prompt_builder=lambda _: "frozen prompt")
    raw = provider({})
    with pytest.raises(ValueError, match="Malformed evidence_summary fields"):
        validate_model_output(raw)
    response_format = payloads[0]["response_format"]
    assert response_format["type"] == "json_schema"
    schema = response_format["json_schema"]["schema"]
    assert schema["additionalProperties"] is False
    assert provider.last_response_diagnostics["evidence_summary_keys"] == ["contradicting_evidence", "supporting"]
    assert provider.last_response_diagnostics["finish_reason"] == "stop"
    assert provider.last_response_diagnostics["json_parse_success"] is True
    assert "secret text" not in json.dumps(provider.last_response_diagnostics)
    # The raw malformed object is never repaired into a different accepted object.
    assert raw["evidence_summary"] == malformed["evidence_summary"]


def test_legacy_provider_path_keeps_json_object_response_format():
    payloads = []

    def transport(payload, api_key, timeout):
        payloads.append(payload)
        return {"choices": [{"message": {"content": json.dumps(valid())}}]}

    provider = QwenProvider(api_key="test-key-not-real", transport=transport)
    provider({})
    assert payloads[0]["response_format"] == {"type": "json_object"}


def _completion(output, finish_reason="stop"):
    return {"model": "qwen-plus", "choices": [{"finish_reason": finish_reason,
            "message": {"content": json.dumps(output)}}]}


def test_success_then_pre_response_failure_clears_diagnostics():
    calls = []

    def transport(payload, api_key, timeout):
        calls.append(payload)
        if len(calls) == 1:
            return _completion(valid())
        raise RuntimeError("transport failed before response")

    provider = QwenProvider(api_key="test-key-not-real", transport=transport)
    provider({})
    assert provider.last_response_diagnostics["json_parse_success"] is True
    with pytest.raises(RuntimeError):
        provider({})
    assert provider.last_response_diagnostics is None


def test_success_then_success_diagnostics_are_current_only():
    outputs = [valid(), {**valid(), "confidence": .7, "explanation": "second"}]

    def transport(payload, api_key, timeout):
        return _completion(outputs.pop(0))

    provider = QwenProvider(api_key="test-key-not-real", transport=transport)
    provider({})
    first_chars = provider.last_response_diagnostics["response_characters"]
    provider({})
    assert provider.last_response_diagnostics["response_characters"] != first_chars
    assert provider.last_response_diagnostics["top_level_keys"] == sorted(valid())


def test_retry_diagnostics_are_scoped_to_one_invocation():
    calls = []

    def transport(payload, api_key, timeout):
        calls.append(payload)
        if len(calls) == 1:
            return _completion(valid(), finish_reason="length")
        return _completion(valid())

    provider = QwenProvider(api_key="test-key-not-real", transport=transport)
    provider({})
    assert len(calls) == 2
    assert provider.last_response_diagnostics["finish_reason"] == "stop"
    assert provider.last_response_diagnostics["truncated"] is False


def test_runner_failure_artifact_does_not_inherit_prior_diagnostics(tmp_path):
    calls = []

    def transport(payload, api_key, timeout):
        calls.append(payload)
        if len(calls) == 1:
            return _completion(valid())
        raise RuntimeError("pre-response transport failure")

    provider = QwenProvider(api_key="test-key-not-real", transport=transport,
                            prompt_builder=lambda _: "frozen prompt")
    transition = generate_transition(1000, D_PLUS)
    control = generate_transition(1000, D_PLUS, control=True)
    with pytest.raises(RuntimeError):
        run_paired_experiment(provider, transition_world=transition,
                               control_world=control, artifact_dir=tmp_path,
                               start=350, end=350)
    failure = json.loads((tmp_path / "failure.json").read_text())
    assert failure["stage"] == "Transition"
    assert failure["timestep"] == 350
    assert failure["provider_diagnostics"] is None
