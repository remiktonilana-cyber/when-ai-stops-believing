"""Reference freeze checks; no canonical E3 world is generated."""
import ast
from pathlib import Path
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from src import lai_transition_reference as ref
from src import lai_transition_calibration as calibration
from src.lai_transition_environment import alpha_schedule


class TransitionReferenceTests(unittest.TestCase):
    def test_frozen_parameters_and_shared_horizon(self):
        self.assertEqual((ref.D_PLUS, ref.DELTA, ref.K, ref.W), (.03, .50, 3, 50))
        self.assertEqual(ref.ALPHA_BOUNDARY, 1.50)
        self.assertEqual(ref.W, calibration.W)
        self.assertEqual((ref.N, ref.T_WARNING, ref.T_STRUCTURAL), (1200, 400, 600))

    def test_boundary_derived_from_unchanged_schedule(self):
        alpha = alpha_schedule()
        np.testing.assert_array_equal(alpha[:600], np.ones(600))
        np.testing.assert_array_equal(alpha[600:900], 1 + 2*np.arange(300)/299)
        np.testing.assert_array_equal(alpha[900:], np.full(300, 3))
        self.assertEqual(ref.T_DELTA, np.flatnonzero(alpha >= ref.ALPHA_BOUNDARY)[0])
        self.assertEqual(ref.T_DELTA, 675)

    def test_selected_evidence_horizon_and_persistence(self):
        rolling = calibration.rolling_evidence(np.ones(52), np.full(52, 2.))
        self.assertEqual(rolling.evaluation_t.tolist(), [50, 51, 52])
        self.assertEqual(calibration.evidence_time(rolling, ref.DELTA, ref.K), 52)
        self.assertIsNone(calibration.evidence_time(rolling.iloc[:2], ref.DELTA, ref.K))
        boundary = pd.DataFrame(dict(evaluation_t=[50, 51, 52], lower=[1.5]*3))
        self.assertIsNone(calibration.evidence_time(boundary, ref.DELTA, ref.K))

    def test_calibration_routine_requests_only_fixed_noncanonical_seeds(self):
        self.assertEqual(calibration.SEEDS, tuple(range(1000, 1200)))
        self.assertNotIn(42, calibration.SEEDS)
        fake = pd.DataFrame(dict(shock=[1.], next_response=[1.]))
        with patch.object(calibration, 'generate_transition', return_value=fake) as generate, \
                patch.object(calibration, 'rolling_evidence', return_value=None), \
                patch.object(calibration, 'evidence_time', return_value=None), \
                patch.object(calibration, 'warning_diagnostic', side_effect=lambda worlds: (pd.DataFrame(), {})), \
                patch.object(calibration, 'summarize_evidence', return_value=pd.DataFrame()), \
                patch('builtins.print'):
            calibration.run_calibration()
        self.assertEqual(generate.call_count, 1600)
        self.assertEqual({call.args[0] for call in generate.call_args_list}, set(range(1000, 1200)))

    def test_e3_imports_have_no_provider_dependency(self):
        allowed = {'pathlib', 'warnings', 'numpy', 'pandas', 'scipy', 'sklearn', 'src'}
        local = {'src.lai_transition_environment', 'src.lai_transition_calibration'}
        for filename in ('lai_transition_environment.py', 'lai_transition_calibration.py',
                         'lai_transition_reference.py'):
            tree = ast.parse((Path(__file__).resolve().parents[1] / 'src' / filename).read_text())
            for node in ast.walk(tree):
                names = [node.module] if isinstance(node, ast.ImportFrom) else (
                    [alias.name for alias in node.names] if isinstance(node, ast.Import) else [])
                for name in names:
                    self.assertIn(name.split('.')[0], allowed)
                    if name.startswith('src.'):
                        self.assertIn(name, local)
