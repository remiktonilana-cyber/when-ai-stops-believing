"""Offline engineering checks; providers and full-run configuration are faked."""
import json
from unittest.mock import Mock, patch

import pytest

from src import lai_qwen_paired_experiment as runner
from tests.test_lai_qwen_paired_experiment import FakeProvider, _worlds, _raw


@pytest.fixture
def run(tmp_path):
    transition, control = _worlds()
    def invoke(provider, **overrides):
        options = dict(transition_world=transition, control_world=control,
                       artifact_dir=tmp_path, start=350, end=352)
        options.update(overrides)
        return runner.run_paired_experiment(provider, **options)
    return invoke


def partial(run):
    with pytest.raises(RuntimeError):
        run(FakeProvider(fail_after=2))


def test_deepseek_configuration():
    with patch('src.deepseek_provider.DeepSeekProvider') as provider, \
         patch.object(runner, 'generate_transition', side_effect=['transition', 'control']) as generate, \
         patch.object(runner, 'run_paired_experiment', return_value='fake result') as paired:
        assert runner.run_deepseek_paired_experiment() == 'fake result'
        provider.assert_called_once_with(model='deepseek-v4-flash', prompt_builder=runner.build_neutral_prompt)
        assert generate.call_args_list[0].args == (42, runner.D_PLUS)
        assert generate.call_args_list[0].kwargs == {'control': False}
        assert generate.call_args_list[1].kwargs == {'control': True}
        options = paired.call_args.kwargs
        assert options['provider_name'] == 'deepseek'
        assert options['model'] == 'deepseek-v4-flash'
        assert options['artifact_dir'] == 'results/lai_deepseek_e63c'
        assert options['experiment_id'] == 'lai_deepseek_e63c_seed42'
        assert (options['start'], options['end']) == (350, 950)


@pytest.mark.parametrize('corruption', ['duplicate', 'truncated', 'gap', 'provenance', 'missing_init', 'pending_write', 'inflight'])
def test_corrupt_checkpoint_rejected_before_calls(run, tmp_path, corruption):
    partial(run)
    path = tmp_path / 'transition_trajectory.jsonl'
    original = path.read_text()
    if corruption == 'duplicate':
        path.write_text(original + original)
    elif corruption == 'truncated':
        path.write_text(original + '{')
    elif corruption in ('gap', 'provenance'):
        record = json.loads(original)
        record['timestep' if corruption == 'gap' else 'provider'] = 351 if corruption == 'gap' else 'other'
        path.write_text(json.dumps(record) + '\n')
    elif corruption == 'missing_init':
        (tmp_path / 'initialization.json').unlink()
    elif corruption == 'pending_write':
        (tmp_path / 'initialization.json.pending-write').write_text('{')
    else:
        (tmp_path / 'inflight.json').write_text(json.dumps({'stage':'Transition','timestep':351}))
    provider = Mock()
    with pytest.raises(ValueError):
        run(provider)
    provider.assert_not_called()


@pytest.mark.parametrize('change', ['provider', 'world', 'range'])
def test_configuration_mismatch_rejected(run, change):
    partial(run)
    options = {}
    if change == 'provider': options['provider_name'] = 'deepseek'
    elif change == 'range': options['end'] = 353
    else:
        world, _ = _worlds()
        world.loc[350, 'shock'] += 1
        options['transition_world'] = world
    provider = Mock()
    with pytest.raises(ValueError, match='configuration'):
        run(provider, **options)
    provider.assert_not_called()


@pytest.mark.parametrize('stage', ['initialization', 'Transition'])
def test_sanitized_failure(run, tmp_path, stage):
    secret = 'DO_NOT_PERSIST_EXCEPTION_OR_DIAGNOSTICS'
    provider = Mock(side_effect=([RuntimeError(secret)] if stage == 'initialization' else [_raw(), RuntimeError(secret)]))
    provider.last_response_diagnostics = {'secret':secret}
    with pytest.raises(RuntimeError):
        run(provider)
    failure = json.loads((tmp_path / 'failure.json').read_text())
    assert failure == {'stage':stage, 'timestep':349 if stage == 'initialization' else 350,
                       'error_category':'provider_failure','technical_retry_count':0,'provider_diagnostics':None}
    assert secret not in ''.join(p.read_text() for p in tmp_path.iterdir() if p.is_file())
    assert not (tmp_path / 'transition_trajectory.jsonl').exists()
    if stage == 'initialization': assert not (tmp_path / 'initialization.json').exists()


def test_actual_format_retry_count_and_no_invalid_belief(run, tmp_path):
    provider = Mock(side_effect=ValueError('malformed structured output: secret payload'))
    with pytest.raises(ValueError): run(provider)
    assert provider.call_count == 2
    failure = json.loads((tmp_path / 'failure.json').read_text())
    assert failure['technical_retry_count'] == 1
    assert 'secret payload' not in json.dumps(failure)
    assert not (tmp_path / 'initialization.json').exists()


def test_atomic_failure_keeps_previous_checkpoint_and_blocks_replay(run, tmp_path):
    partial(run)
    path = tmp_path / 'transition_trajectory.jsonl'
    before = path.read_bytes()
    replace = runner.os.replace
    def fail_replace(source, destination):
        if destination == path: raise OSError('synthetic interrupted write')
        return replace(source, destination)
    provider = Mock(return_value=_raw())
    with patch.object(runner.os, 'replace', side_effect=fail_replace):
        with pytest.raises(OSError): run(provider)
    assert provider.call_count == 1
    assert path.read_bytes() == before
    retry = Mock()
    with pytest.raises(ValueError, match='incomplete atomic'): run(retry)
    retry.assert_not_called()


def test_resume_exact_next_step_and_committed_inflight(run, tmp_path):
    partial(run)
    (tmp_path / 'inflight.json').write_text(json.dumps({'stage':'Transition','timestep':350}))
    provider = Mock(return_value=_raw())
    run(provider)
    assert provider.call_count == 5  # Transition 351..352 + Control 350..352
    assert provider.call_args_list[0].args[0]['historical_summary']['resolved_count'] == 351
    no_calls = Mock()
    run(no_calls)
    no_calls.assert_not_called()
    for name in ['transition', 'control']:
        records = [json.loads(line) for line in (tmp_path / f'{name}_trajectory.jsonl').read_text().splitlines()]
        assert [r['timestep'] for r in records] == [350,351,352]


def test_concurrent_writer_rejected(run, tmp_path):
    with (tmp_path / '.runtime.lock').open('a') as lock:
        runner.fcntl.flock(lock, runner.fcntl.LOCK_EX | runner.fcntl.LOCK_NB)
        provider = Mock()
        with pytest.raises(ValueError, match='already in use'): run(provider)
        provider.assert_not_called()


@pytest.mark.parametrize('filename', ['initialization.json', 'run_metadata.json'])
def test_null_checkpoint_never_treated_as_missing(run, tmp_path, filename):
    partial(run)
    (tmp_path / filename).write_text('null')
    provider = Mock()
    with pytest.raises(ValueError, match='invalid checkpoint object'): run(provider)
    provider.assert_not_called()


def test_successful_initialization_persistence_failure_blocks_reinitialization(run, tmp_path):
    replace = runner.os.replace
    def interrupted(source, destination):
        if destination.name == 'initialization.json': raise OSError('interrupted')
        return replace(source, destination)
    provider = Mock(return_value=_raw())
    with patch.object(runner.os, 'replace', side_effect=interrupted):
        with pytest.raises(OSError): run(provider)
    assert provider.call_count == 1
    retry = Mock()
    with pytest.raises(ValueError): run(retry)
    retry.assert_not_called()
