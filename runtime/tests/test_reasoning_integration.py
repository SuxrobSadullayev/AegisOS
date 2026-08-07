import unittest
from runtime.src.config import AegisConfig, ReasoningDepth
from runtime.src.reasoning import (
    ReasoningPipeline,
    DecisionGraph,
    ReasoningNode,
    NodeType,
    SelfReview
)


class TestReasoningIntegration(unittest.TestCase):
    def setUp(self):
        self.config = AegisConfig.load_from_env()
        self.pipeline = ReasoningPipeline(self.config)

    def test_conflict_detection_and_rejection(self):
        graph = DecisionGraph()
        graph.add_node(ReasoningNode("N1", NodeType.GOAL, "Goal"))
        # Introduce conflicting constraints
        graph.add_node(ReasoningNode("N2", NodeType.CONSTRAINT, "Must lock network connection"))
        graph.add_node(ReasoningNode("N3", NodeType.CONSTRAINT, "No lock allowed on network"))

        reviewer = SelfReview()
        is_approved, comments = reviewer.review(graph, confidence=0.85, threshold=0.70)
        self.assertFalse(is_approved)
        self.assertIn("Conflict between N2 and N3", comments[0])

    def test_l3_deep_reasoning_integration(self):
        result = self.pipeline.run("Redesign global distributed database architecture", depth=ReasoningDepth.L3_DEEP)
        self.assertEqual(result.plan.depth, ReasoningDepth.L3_DEEP)
        self.assertTrue(result.is_approved)
        self.assertIn("NODE_DECISION_1", result.plan.ordered_steps)


if __name__ == '__main__':
    unittest.main()
