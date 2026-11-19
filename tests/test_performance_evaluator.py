"""
Unit and integration tests for BankFlow AI Performance Evaluation Framework (Phase 10)
"""

import os
import json
import csv
import pytest
from app.simulation.performance_evaluator import PerformanceEvaluator, ResourceSampler


def test_resource_sampler():
    """Verifies resource sampler captures process CPU and memory metrics."""
    sampler = ResourceSampler()
    sampler.sample()
    metrics = sampler.get_summary()

    assert "cpu_peak_percent" in metrics
    assert "cpu_avg_percent" in metrics
    assert "memory_peak_mb" in metrics
    assert "memory_avg_mb" in metrics
    assert isinstance(metrics["memory_peak_mb"], (int, float))


def test_evaluator_single_run_p1(db_session):
    """Verifies single run execution and operational metrics computation."""
    evaluator = PerformanceEvaluator(db=db_session)
    res = evaluator.run_single_experiment("P1", workload=4, pool_size=2, max_ticks=20)

    assert res["scenario_id"] == "P1"
    assert res["scenario_name"] == "Concurrent Arrivals"
    assert res["workload_size"] == 4
    assert res["agent_pool_size"] == 2
    assert res["total_execution_time_seconds"] > 0
    assert res["throughput_rpm"] >= 0
    assert res["avg_latency_seconds"] >= 0
    assert res["max_latency_seconds"] >= 0
    assert "agent_idle_percent" in res
    assert "cpu_peak_percent" in res
    assert "memory_peak_mb" in res
    assert res["completed_requests"] >= 0


def test_evaluator_export(tmp_path, db_session):
    """Verifies results export to CSV and JSON formats."""
    evaluator = PerformanceEvaluator(db=db_session)
    sample_results = [
        {
            "scenario_id": "P1",
            "scenario_name": "Concurrent Arrivals",
            "workload_size": 10,
            "agent_pool_size": 4,
            "total_execution_time_seconds": 5.2,
            "throughput_rpm": 115.3,
            "avg_latency_seconds": 3.1,
            "max_latency_seconds": 4.9,
            "failure_recovery_time_seconds": 0.0,
            "federation_latency_ms": 0.0,
            "agent_idle_percent": 35.0,
            "cpu_peak_percent": 15.2,
            "cpu_avg_percent": 8.4,
            "memory_peak_mb": 140.2,
            "memory_avg_mb": 139.8,
            "completed_requests": 10,
            "failed_requests": 0,
            "total_requests": 10,
            "success_rate_percent": 100.0,
            "timestamp": "2026-11-19T10:00:00Z",
        }
    ]

    csv_out = str(tmp_path / "test_results.csv")
    json_out = str(tmp_path / "test_results.json")

    evaluator.export_results(sample_results, csv_filename=csv_out, json_filename=json_out)

    assert os.path.exists(csv_out)
    assert os.path.exists(json_out)

    with open(csv_out, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["scenario_id"] == "P1"
        assert float(rows[0]["throughput_rpm"]) == 115.3

    with open(json_out, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert data["metadata"]["system"] == "BankFlow AI"
        assert len(data["results"]) == 1
        assert data["summary"]["max_throughput_rpm"] == 115.3
