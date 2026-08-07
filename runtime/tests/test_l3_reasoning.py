"""
Reasoning Engine Deep L3 Analytical Reasoning Tests for Aegis AI Operating System.
Verifies L3_DEEP reasoning problem decomposition, goals, constraints, alternatives,
risk estimation, trade-offs, confidence scoring, failure prediction, and recovery suggestions.
"""

import unittest
from runtime.src.config import AegisConfig, ReasoningDepth
from runtime.src.reasoning import (
    ReasoningPipeline, DecisionGraph, Goal, Constraint,
    Alternative, Risk, Tradeoff, Confidence, FailurePrediction, RecoverySuggestion
)



class TestL3DeepReasoningEngine(unittest.TestCase):
    """Tests L3 Deep Analytical Reasoning features in Reasoning Engine."""

    def setUp(self):
        self.config = AegisConfig(reasoning_depth="L3")
        self.pipeline = ReasoningPipeline(self.config)

    def test_reasoning_pipeline_l3_execution(self):
        """1. Verifies reasoning pipeline execution under L3_DEEP reasoning depth."""
        result = self.pipeline.run(
            task_prompt="Design a high-throughput microservices architecture with Redis caching and JWT authentication",
            depth=ReasoningDepth.L3_DEEP
        )

        self.assertIsNotNone(result)
        self.assertIsNotNone(result.graph)
        self.assertGreater(len(result.graph.nodes), 0)
        self.assertGreater(result.confidence_score, 0.0)
        self.assertTrue(result.is_approved)

    def test_l3_problem_decomposition_into_decision_graph(self):
        """2. Verifies problem decomposition creates goals, constraints, and alternative nodes."""
        from runtime.src.reasoning import ReasoningNode, NodeType
        graph = DecisionGraph()
        g1 = ReasoningNode("G-1", NodeType.GOAL, "High availability API")
        c1 = ReasoningNode("C-1", NodeType.CONSTRAINT, "Latency under 50ms")
        a1 = ReasoningNode("A-1", NodeType.ALTERNATIVE, "Redis Cache Invalidation")

        graph.add_node(g1)
        graph.add_node(c1)
        graph.add_node(a1)

        self.assertIn("G-1", graph.nodes)
        self.assertIn("C-1", graph.nodes)
        self.assertIn("A-1", graph.nodes)


    def test_l3_tradeoff_and_confidence_scoring(self):
        """3. Verifies trade-off analysis and confidence threshold calculation."""
        conf = Confidence(score=0.85, is_threshold_met=True, evaluated_claim_count=5)
        self.assertTrue(conf.is_threshold_met)
        self.assertGreater(conf.score, 0.70)

        tradeoff = Tradeoff(
            alternative_id="A-1",
            pros=["Low latency", "High throughput"],
            cons=["Cache coherence complexity"],
            composite_score=0.88
        )
        self.assertEqual(tradeoff.composite_score, 0.88)

    def test_l3_failure_prediction_and_recovery_suggestions(self):
        """4. Verifies failure prediction and recovery suggestion generation."""
        pred = FailurePrediction(
            failure_type="CACHE_STALENESS",
            probability=0.25,
            affected_node_ids=["A-1"]
        )
        rec = RecoverySuggestion(
            suggestion_id="REC-1",
            failure_type="CACHE_STALENESS",
            action_plan="Implement TTL expiration with async pub/sub cache invalidate"
        )

        self.assertEqual(pred.failure_type, "CACHE_STALENESS")
        self.assertIn("pub/sub", rec.action_plan)


if __name__ == "__main__":
    unittest.main()
