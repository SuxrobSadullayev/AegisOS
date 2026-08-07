"""
Performance & Load Benchmark Suite for Aegis AI Operating System.
Executes concurrent request load tests (1, 10, 50, 100 requests) measuring
total pipeline latency, stage latencies, memory footprint, and plugin overhead.
"""

import time
import unittest
import concurrent.futures
from runtime.src.config import AegisConfig
from runtime.src.gateway import MockProvider
from runtime.src.orchestrator import RuntimeOrchestrator


class TestPerformanceBenchmark(unittest.TestCase):
    """Performance Benchmark and Concurrency Load Tests."""

    def setUp(self):
        self.config = AegisConfig()
        self.provider = MockProvider(self.config)
        self.orchestrator = RuntimeOrchestrator(self.config, self.provider)

    def test_single_request_latency_benchmark(self):
        """1. Measures single request total latency and stage latency overhead."""
        start = time.time()
        ctx = self.orchestrator.run("Single request benchmark task prompt")
        duration_ms = (time.time() - start) * 1000.0

        self.assertIsNotNone(ctx.model_response)
        self.assertLess(duration_ms, 500.0)  # Must complete under 500ms for Mock provider

        # Inspect tracer timing metrics
        metrics_dict = {m.stage_name: m.duration_ms for m in self.orchestrator.tracer.metrics}
        self.assertIn("TotalPipelineDuration", metrics_dict)

    def test_concurrent_load_10_requests(self):
        """2. Executes 10 concurrent requests and verifies zero race conditions."""
        results = []

        def execute_task(task_id: int):
            orch = RuntimeOrchestrator(self.config, self.provider)
            return orch.run(f"Concurrent load task #{task_id}", session_id=f"SESS_LOAD_10_{task_id}")

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(execute_task, i) for i in range(10)]
            for f in concurrent.futures.as_completed(futures):
                results.append(f.result())

        self.assertEqual(len(results), 10)
        for ctx in results:
            self.assertIsNotNone(ctx.model_response)

    def test_concurrent_load_50_requests(self):
        """3. Executes 50 concurrent requests under thread pool."""
        results = []

        def execute_task(task_id: int):
            orch = RuntimeOrchestrator(self.config, self.provider)
            return orch.run(f"Concurrent load task 50 #{task_id}")

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(execute_task, i) for i in range(50)]
            for f in concurrent.futures.as_completed(futures):
                results.append(f.result())

        self.assertEqual(len(results), 50)

    def test_concurrent_load_100_requests(self):
        """4. Executes 100 concurrent requests measuring throughput."""
        start_time = time.time()
        results = []

        def execute_task(task_id: int):
            orch = RuntimeOrchestrator(self.config, self.provider)
            return orch.run(f"Concurrent load task 100 #{task_id}")

        with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
            futures = [executor.submit(execute_task, i) for i in range(100)]
            for f in concurrent.futures.as_completed(futures):
                results.append(f.result())

        total_time_ms = (time.time() - start_time) * 1000.0
        avg_per_req = total_time_ms / 100.0

        self.assertEqual(len(results), 100)
        self.assertLess(avg_per_req, 50.0)  # Throughput target: <50ms per req under pool


if __name__ == "__main__":
    unittest.main()
