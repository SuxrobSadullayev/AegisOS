"""
Observability Metrics Tests for Aegis AI OS.
Verifies MetricsCollector counters, latency percentiles (p50, p95, p99),
empty dataset handling, single sample edge cases, and thread safety.
"""

import threading
import unittest
from runtime.src.observability import MetricsCollector


class TestObservabilityMetrics(unittest.TestCase):
    """Telemetry metrics and percentile calculation tests."""

    def setUp(self):
        self.collector = MetricsCollector()

    def test_1_counter_increment_default(self):
        """1. Verifies incrementing counters by default amount of 1."""
        self.collector.increment("requests.total")
        self.collector.increment("requests.total")
        summary = self.collector.get_metrics_summary()
        self.assertEqual(summary["counters"]["requests.total"], 2)

    def test_2_counter_increment_custom_amount(self):
        """2. Verifies incrementing counters by specified custom integer amounts."""
        self.collector.increment("tokens.used", 150)
        self.collector.increment("tokens.used", 250)
        summary = self.collector.get_metrics_summary()
        self.assertEqual(summary["counters"]["tokens.used"], 400)

    def test_3_percentile_empty_dataset(self):
        """3. Verifies percentile calculation returns 0.0 when no latencies recorded."""
        self.assertEqual(self.collector.get_percentile("non_existent", 50.0), 0.0)
        self.assertEqual(self.collector.get_percentile("non_existent", 95.0), 0.0)
        self.assertEqual(self.collector.get_percentile("non_existent", 99.0), 0.0)

    def test_4_percentile_single_sample(self):
        """4. Verifies percentile calculation with a single latency sample."""
        self.collector.record_latency("stage.latency", 42.5)
        self.assertEqual(self.collector.get_percentile("stage.latency", 50.0), 42.5)
        self.assertEqual(self.collector.get_percentile("stage.latency", 95.0), 42.5)
        self.assertEqual(self.collector.get_percentile("stage.latency", 99.0), 42.5)

    def test_5_percentile_hundred_samples_accuracy(self):
        """5. Verifies p50, p95, p99 percentiles across 100 uniform samples (1ms to 100ms)."""
        for i in range(1, 101):
            self.collector.record_latency("pipeline.duration", float(i))

        p50 = self.collector.get_percentile("pipeline.duration", 50.0)
        p95 = self.collector.get_percentile("pipeline.duration", 95.0)
        p99 = self.collector.get_percentile("pipeline.duration", 99.0)

        self.assertEqual(p50, 50.5)
        self.assertEqual(p95, 95.05)
        self.assertEqual(p99, 99.01)

    def test_6_metrics_summary_statistics(self):
        """6. Verifies metrics summary contains count, average, p50, p95, p99."""
        self.collector.record_latency("reasoning.l3", 10.0)
        self.collector.record_latency("reasoning.l3", 20.0)
        self.collector.record_latency("reasoning.l3", 30.0)

        summary = self.collector.get_metrics_summary()
        stats = summary["latencies"]["reasoning.l3"]

        self.assertEqual(stats["count"], 3)
        self.assertEqual(stats["avg"], 20.0)
        self.assertEqual(stats["p50"], 20.0)

    def test_7_concurrent_metric_recording_thread_safety(self):
        """7. Verifies concurrent multi-threaded counter and latency recording."""
        def record_worker():
            for i in range(50):
                self.collector.increment("concurrent.calls")
                self.collector.record_latency("concurrent.lat", float(i))

        threads = [threading.Thread(target=record_worker) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        summary = self.collector.get_metrics_summary()
        self.assertEqual(summary["counters"]["concurrent.calls"], 200)
        self.assertEqual(summary["latencies"]["concurrent.lat"]["count"], 200)

    def test_8_multiple_distinct_latency_metrics(self):
        """8. Verifies MetricsCollector tracks distinct metric names independently."""
        self.collector.record_latency("stage.intent", 1.2)
        self.collector.record_latency("stage.model", 150.0)

        summary = self.collector.get_metrics_summary()
        self.assertIn("stage.intent", summary["latencies"])
        self.assertIn("stage.model", summary["latencies"])
        self.assertEqual(summary["latencies"]["stage.intent"]["avg"], 1.2)
        self.assertEqual(summary["latencies"]["stage.model"]["avg"], 150.0)

    def test_9_zero_latency_values(self):
        """9. Verifies zero duration latency values are recorded accurately."""
        self.collector.record_latency("fast.stage", 0.0)
        self.assertEqual(self.collector.get_percentile("fast.stage", 50.0), 0.0)

    def test_10_repeated_identical_values(self):
        """10. Verifies percentiles when all recorded samples have identical latency."""
        for _ in range(20):
            self.collector.record_latency("constant.latency", 15.0)

        self.assertEqual(self.collector.get_percentile("constant.latency", 50.0), 15.0)
        self.assertEqual(self.collector.get_percentile("constant.latency", 95.0), 15.0)


if __name__ == "__main__":
    unittest.main()
