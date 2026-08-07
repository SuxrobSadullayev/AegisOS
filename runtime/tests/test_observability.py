"""
Observability & Pipeline Timing Metrics Tests for Aegis AI Operating System.
Verifies real-time event bus subscriptions, visual progress logs, timing metrics collection,
and trace logging.
"""

import unittest
from runtime.src.config import AegisConfig
from runtime.src.gateway import MockProvider
from runtime.src.orchestrator import RuntimeOrchestrator, PipelineEvent


class TestObservabilityAndMetrics(unittest.TestCase):
    """Tests runtime observability, event bus notifications, and stage metrics."""

    def setUp(self):
        self.config = AegisConfig(verbose=True)
        self.provider = MockProvider(self.config)
        self.orchestrator = RuntimeOrchestrator(self.config, self.provider)

    def test_pipeline_event_bus_publishing(self):
        """1. Verifies EventBus receives events for all pipeline stages."""
        received_events = []

        def event_handler(evt: PipelineEvent):
            received_events.append(evt)

        self.orchestrator.event_bus.subscribe(event_handler)
        self.orchestrator.run("Observability test prompt", session_id="SESS_OBS_1")

        self.assertGreater(len(received_events), 10)
        event_types = [e.event_type for e in received_events]
        self.assertIn("PIPELINE_START", event_types)
        self.assertIn("STAGE_START", event_types)
        self.assertIn("STAGE_SUCCESS", event_types)
        self.assertIn("PIPELINE_COMPLETE", event_types)

    def test_stage_timing_metrics_recording(self):
        """2. Verifies stage timing metrics are recorded accurately by PipelineTracer."""
        self.orchestrator.run("Stage timing metrics task", session_id="SESS_OBS_2")

        metrics = self.orchestrator.tracer.metrics
        self.assertTrue(len(metrics) >= 10)

        recorded_stages = [m.stage_name for m in metrics]
        self.assertIn("IntentResolverStage", recorded_stages)
        self.assertIn("TaskPlannerStage", recorded_stages)
        self.assertIn("KnowledgeLoaderStage", recorded_stages)
        self.assertIn("ReasoningEngineStage", recorded_stages)
        self.assertIn("TruthEngineStage", recorded_stages)
        self.assertIn("PromptComposerStage", recorded_stages)
        self.assertIn("ModelGatewayStage", recorded_stages)
        self.assertIn("QualityEngineStage", recorded_stages)
        self.assertIn("TotalPipelineDuration", recorded_stages)

        for m in metrics:
            self.assertGreaterEqual(m.duration_ms, 0.0)

    def test_tracer_checkpoint_persistence_and_retrieval(self):
        """3. Verifies context checkpoints saved at each stage can be retrieved."""
        ctx = self.orchestrator.run("Checkpoint retrieval task", session_id="SESS_OBS_3")

        checkpoint = self.orchestrator.tracer.get_checkpoint("ReasoningEngineStage")
        self.assertIsNotNone(checkpoint)
        self.assertEqual(checkpoint.user_prompt, "Checkpoint retrieval task")



if __name__ == "__main__":
    unittest.main()
