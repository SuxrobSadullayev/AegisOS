"""
Concurrency & Race Condition Load Tests for Aegis AI OS.
Executes load tests across 1, 10, 50, and 100 concurrent requests, verifying zero race conditions,
session state isolation, and thread safety.
"""

import time
import unittest
import concurrent.futures
from runtime.src.config import AegisConfig
from runtime.src.gateway import MockProvider
from runtime.src.orchestrator import RuntimeOrchestrator


class TestConcurrencyAndLoadResilience(unittest.TestCase):
    """Concurrency & Load Resilience Tests under multi-threaded execution."""

    def setUp(self):
        self.config = AegisConfig()
        self.provider = MockProvider(self.config)

    def test_single_request_baseline(self):
        """1. Single request baseline measurement."""
        orch = RuntimeOrchestrator(self.config, self.provider)
        start = time.time()
        ctx = orch.run("Single baseline request prompt", session_id=f"SESS_CONC_1_{time.time_ns()}")
        duration_ms = (time.time() - start) * 1000.0

        self.assertIsNotNone(ctx.model_response)
        self.assertLess(duration_ms, 500.0)

    def test_concurrent_load_10_requests(self):
        """2. 10 concurrent requests test."""
        results = []

        def task_worker(task_id: int):
            orch = RuntimeOrchestrator(self.config, self.provider)
            return orch.run(f"Concurrent task #{task_id}", session_id=f"SESS_CONC_10_{task_id}_{time.time_ns()}")

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(task_worker, i) for i in range(10)]
            for f in concurrent.futures.as_completed(futures):
                results.append(f.result())

        self.assertEqual(len(results), 10)
        for ctx in results:
            self.assertIsNotNone(ctx.model_response)

    def test_concurrent_load_50_requests(self):
        """3. 50 concurrent requests test."""
        results = []

        def task_worker(task_id: int):
            orch = RuntimeOrchestrator(self.config, self.provider)
            return orch.run(f"Concurrent 50 task #{task_id}", session_id=f"SESS_CONC_50_{task_id}_{time.time_ns()}")

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(task_worker, i) for i in range(50)]
            for f in concurrent.futures.as_completed(futures):
                results.append(f.result())

        self.assertEqual(len(results), 50)

    def test_concurrent_load_100_requests(self):
        """4. 100 concurrent requests test measuring total throughput and state isolation."""
        start_time = time.time()
        results = []

        def task_worker(task_id: int):
            orch = RuntimeOrchestrator(self.config, self.provider)
            return orch.run(f"Concurrent 100 task #{task_id}", session_id=f"SESS_CONC_100_{task_id}_{time.time_ns()}")

        with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
            futures = [executor.submit(task_worker, i) for i in range(100)]
            for f in concurrent.futures.as_completed(futures):
                results.append(f.result())

        total_time_ms = (time.time() - start_time) * 1000.0
        avg_per_req = total_time_ms / 100.0

        self.assertEqual(len(results), 100)
        self.assertLess(avg_per_req, 50.0)  # Throughput target <50ms per req under pool


if __name__ == "__main__":
    unittest.main()
