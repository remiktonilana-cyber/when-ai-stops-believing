"""Human-selected E3.4 reference; no generation, fitting, or Agent execution.

Import these constants for the fixed design; the calibration candidate grid
remains historical calibration configuration. Benchmark times are hidden truth,
not Agent inputs. T_evidence is trajectory-dependent and is not assigned here.
"""
from src.lai_transition_environment import N, T_WARNING, T_STRUCTURAL
from src.lai_transition_calibration import W, theoretical_time

D_PLUS = 0.03
DELTA = 0.50
K = 3
ALPHA_BOUNDARY = 1 + DELTA
T_DELTA = theoretical_time(DELTA)
