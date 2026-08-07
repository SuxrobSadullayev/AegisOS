import unittest
from runtime.src.config import AegisConfig, EpistemicState, EvidenceLevel
from runtime.src.gateway import MockProvider
from runtime.src.orchestrator import RuntimeOrchestrator

class TestOrchestratorIntegration(unittest.TestCase):
    def setUp(self):
        self.config = AegisConfig(max_retries=3)
        self.provider = MockProvider(self.config)
        self.orchestrator = RuntimeOrchestrator(self.config, self.provider)

    def test_end_to_end_orchestrator_flow(self):
        # Pre-populate claim graph in orchestrator store
        self.orchestrator.graph_store.create_claim(
            "Database pool size verified",
            state=EpistemicState.VERIFIED_FACT,
            evidence_level=EvidenceLevel.LEVEL_3_CODE_INSPECTION
        )

        final_context = self.orchestrator.run("Refactor Python database pool with mutex")
        self.assertIsNotNone(final_context.resolved_context)
        self.assertIsNotNone(final_context.engine_trace)
        self.assertIsNotNone(final_context.composed_prompt)
        self.assertIsNotNone(final_context.model_response)
        self.assertEqual(final_context.quality_result.status.value, "PASS")

        # Verify tracer metrics
        metrics = self.orchestrator.tracer.metrics
        stage_names = [m.stage_name for m in metrics]
        self.assertIn("IntentResolverStage", stage_names)
        self.assertIn("ReasoningEngineStage", stage_names)
        self.assertIn("QualityEngineStage", stage_names)

if __name__ == '__main__':
    unittest.main()
