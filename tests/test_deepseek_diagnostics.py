"""Offline output-diagnostics tests; no network or persisted experiment access."""
import json
from copy import deepcopy
from unittest.mock import Mock

import pytest

from src.deepseek_provider import DeepSeekProvider
from src.lai_output_diagnostics import safe_diagnostics
from src.lai_qwen_paired_experiment import _call_and_checkpoint
from tests.test_deepseek_provider import MODEL_OUTPUT, RecordingTransport, SequenceTransport


@pytest.mark.parametrize('case,category,retries', [
    ('json','invalid_json',1), ('array','top_level_type',1),
    ('missing','missing_fields',0), ('extra','schema_mismatch',0),
    ('evidence_keys','evidence_structure_mismatch',1),
    ('evidence_type','evidence_structure_mismatch',1),
    ('list_type','evidence_structure_mismatch',0),
    ('item_type','item_type_mismatch',0),
    ('limit','evidence_item_limit',0),
    ('confidence','field_type_mismatch',0),
    ('status','field_value_invalid',0),
])
def test_failure_metadata_and_unchanged_retry_behavior(tmp_path, case, category, retries):
    secret='SENSITIVE_VALUE_DO_NOT_PERSIST'
    output=deepcopy(MODEL_OUTPUT)
    output['explanation']=secret
    if case=='array': output=[]
    elif case=='missing': del output['confidence']
    elif case=='extra': output[secret]=secret
    elif case=='evidence_keys': output['evidence_summary']={secret:secret}
    elif case=='evidence_type': output['evidence_summary']=secret
    elif case=='list_type': output['evidence_summary']['supporting_evidence']=secret
    elif case=='item_type': output['evidence_summary']['supporting_evidence']=[{secret:secret}]
    elif case=='limit': output['evidence_summary']['supporting_evidence']=[secret]*4
    elif case=='confidence': output['confidence']=secret
    elif case=='status': output['belief_status']=secret
    transport=RecordingTransport(secret if case=='json' else json.dumps(output))
    provider=DeepSeekProvider(api_key=secret,transport=transport)
    persist=Mock()
    with pytest.raises(ValueError):
        _call_and_checkpoint(provider,{},tmp_path,'Transition',715,persist)
    persist.assert_not_called()
    assert len(transport.payloads)==1+retries
    raw=(tmp_path/'failure.json').read_text()
    assert secret not in raw
    failure=json.loads(raw)
    diag=failure['provider_diagnostics']
    assert failure['technical_retry_count']==retries
    assert diag['validation_category']==category
    assert diag['json_parse_success'] is (case!='json')
    assert not (tmp_path/'inflight.json').exists()
    if case=='item_type':
        assert diag['evidence_item_types']['supporting_evidence']==['object']
    if case=='missing':
        assert diag['field_presence']['confidence'] is False
        assert diag['field_types']['confidence']=='missing'
    if case=='extra': assert '<redacted_unknown_key>' in diag['top_level_keys']


def test_success_then_failure_clears_diagnostics(tmp_path):
    response={'choices':[{'message':{'content':json.dumps(MODEL_OUTPUT)}}]}
    provider=DeepSeekProvider(api_key='fake',transport=SequenceTransport([response,RuntimeError('secret')]))
    assert provider({})==MODEL_OUTPUT
    assert provider.last_response_diagnostics['validation_category']=='no_shape_error_detected'
    with pytest.raises(RuntimeError):
        _call_and_checkpoint(provider,{},tmp_path,'initialization',349,Mock())
    assert provider.last_response_diagnostics is None
    assert json.loads((tmp_path/'failure.json').read_text())['provider_diagnostics'] is None


def test_retry_diagnostics_describe_final_attempt(tmp_path):
    response={'choices':[{'message':{'content':'invalid json secret'}}]}
    output=deepcopy(MODEL_OUTPUT)
    output['evidence_summary']['supporting_evidence']=[99]
    last={'choices':[{'message':{'content':json.dumps(output)}}]}
    provider=DeepSeekProvider(api_key='fake',transport=SequenceTransport([response,last]))
    with pytest.raises(ValueError):
        _call_and_checkpoint(provider,{},tmp_path,'initialization',349,Mock())
    failure=json.loads((tmp_path/'failure.json').read_text())
    assert failure['provider_diagnostics']['validation_category']=='item_type_mismatch'
    assert failure['provider_diagnostics']['json_parse_success'] is True
    assert failure['technical_retry_count']==1


def test_untrusted_diagnostics_are_projected():
    secret='untrusted secret'
    diag=safe_diagnostics({'json_parse_success':True,'raw_response':secret,
                          'top_level_keys':['confidence',secret], 'validation_category':secret,
                          'field_types':{'confidence':secret},'evidence_item_types':{'supporting_evidence':[secret,'string']}})
    assert secret not in json.dumps(diag)
    assert 'raw_response' not in diag


def test_envelope_failure_is_identified_without_response_content():
    provider=DeepSeekProvider(api_key='fake',transport=lambda *args:{'secret':'do not persist'})
    with pytest.raises(ValueError): provider({})
    assert provider.last_response_diagnostics['validation_category']=='response_envelope'
    assert provider.last_response_diagnostics['json_parse_success'] is None
