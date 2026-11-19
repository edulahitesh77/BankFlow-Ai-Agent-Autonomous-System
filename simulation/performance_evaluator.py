"""
BankFlow AI - Performance Evaluator Shim
Routes execution to backend.app.simulation.performance_evaluator
"""

import sys
import os

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.simulation.performance_evaluator import PerformanceEvaluator, ResourceSampler

if __name__ == "__main__":
    evaluator = PerformanceEvaluator()
    evaluator.run_full_evaluation()
