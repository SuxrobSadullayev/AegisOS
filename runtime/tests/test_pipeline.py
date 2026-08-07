import unittest
from runtime.src.config import AegisConfig, EpistemicState, EvidenceLevel, ReasoningDepth
from runtime.src.epistemic import EpistemicGraphStore
from runtime.src.resolver import ResolvedContext
from runtime.src.pipeline import EnginePipeline

class TestEnginePipeline(unittest.TestCase):
    def setUp(self):
        self.config = AegisConfig.load_from_env()
        self.store = EpistemicGraphStore()
        self.pipeline = EnginePipeline(self.config, self.store)

    def test_pipeline_execution_pass(self):
        c1 = self.store.create_claim("Config exists", EpistemicState.VERIFIED_FACT, EvidenceLevel.LEVEL_3_CODE_INSPECTION)
        resolved_ctx = ResolvedContext(target_modules=[], reasoning_depth=ReasoningDepth.L2_STANDARD)
        trace = self.pipeline.execute("Refactor database pool", resolved_ctx)
        self.assertTrue(trace.gate_passed)
        self.assertGreaterEqual(trace.confidence_score, 0.70)
        self.assertIn("Decomposition", trace.steps_executed)

    def test_pipeline_execution_low_confidence_fail(self):
        # Create unverified / invalidated claims to drop confidence below 0.70
        self.store.create_claim("Unknown claim 1", EpistemicState.INVALIDATED, EvidenceLevel.LEVEL_0_UNSUBSTANTIATED)
        self.store.create_claim("Unknown claim 2", EpistemicState.SUSPECT, EvidenceLevel.LEVEL_0_UNSUBSTANTIATED)
        resolved_ctx = ResolvedContext(target_modules=[], reasoning_depth=ReasoningDepth.L3_DEEP)
        trace = self.pipeline.execute("Redesign architecture", resolved_ctx)
        self.assertFalse(trace.gate_passed)
        self.assertLess(trace.confidence_score, 0.70)

if __name__ == '__main__':
    unittest.main()
