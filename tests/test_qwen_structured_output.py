import json

import pytest

from src.qwen_provider import LAI_AGENT_BELIEF_JSON_SCHEMA, QwenProvider
from src.universal_llm_adapter import validate_model_output


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

