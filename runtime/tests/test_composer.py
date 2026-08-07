import unittest
from runtime.src.config import AegisConfig, ReasoningDepth
from runtime.src.resolver import ResolvedContext
from runtime.src.pipeline import EnginePipelineTrace
from runtime.src.composer import PromptComposer

class TestPromptComposer(unittest.TestCase):
    def setUp(self):
        self.config = AegisConfig.load_from_env()
        self.composer = PromptComposer(self.config)

    def test_compose_payload(self):
        resolved_ctx = ResolvedContext(
            target_modules=["modules/domains/languages/python/standards.md"],
            reasoning_depth=ReasoningDepth.L2_STANDARD
        )
        trace = EnginePipelineTrace(
            depth=ReasoningDepth.L2_STANDARD,
            steps_executed=["Decomposition", "Planning"],
            confidence_score=0.85,
            claims_verified=["CLM-000001"],
            gate_passed=True
        )
        payload = self.composer.compose(resolved_ctx, trace)
        self.assertIn("LAYER 0: AEGIS KERNEL CONTEXT", payload)
        self.assertIn("Reasoning Depth: L2", payload)
        self.assertIn("Python Engineering Standards", payload)

if __name__ == '__main__':
    unittest.main()
