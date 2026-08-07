import unittest
from runtime.src.config import AegisConfig, ReasoningDepth
from runtime.src.reasoning import (
    ReasoningNode,
    NodeType,
    DecisionGraph,
    AlternativeGenerator,
    RiskAnalyzer,
    ConfidenceEstimator,
    SelfReview,
    ReasoningPipeline,
    ReasoningResult
)


class TestReasoningEngine(unittest.TestCase):
    def setUp(self):
        self.config = AegisConfig.load_from_env()
        self.pipeline = ReasoningPipeline(self.config)

    def test_decision_graph_topological_sort(self):
        graph = DecisionGraph()
        n1 = ReasoningNode("N1", NodeType.GOAL, "Goal")
        n2 = ReasoningNode("N2", NodeType.SUBPROBLEM, "Subproblem", dependencies=["N1"])
        n3 = ReasoningNode("N3", NodeType.DECISION, "Decision", dependencies=["N2"])

        graph.add_node(n1)
        graph.add_node(n2)
        graph.add_node(n3)

        ordered = graph.topological_sort()
        self.assertEqual(ordered, ["N1", "N2", "N3"])

    def test_decision_graph_cycle_detection(self):
        graph = DecisionGraph()
        n1 = ReasoningNode("N1", NodeType.GOAL, "Goal", dependencies=["N2"])
        n2 = ReasoningNode("N2", NodeType.SUBPROBLEM, "Subproblem", dependencies=["N1"])

        graph.add_node(n1)
        graph.add_node(n2)

        with self.assertRaises(ValueError):
            graph.topological_sort()

    def test_alternative_generator(self):
        gen = AlternativeGenerator()
        subprob = ReasoningNode("SP1", NodeType.SUBPROBLEM, "Implement auth service")
        alts = gen.generate(subprob)
        self.assertEqual(len(alts), 2)
        self.assertEqual(alts[0].node_type, NodeType.ALTERNATIVE)

    def test_confidence_estimator(self):
        graph = DecisionGraph()
        graph.add_node(ReasoningNode("N1", NodeType.GOAL, "Goal", confidence=1.0))
        graph.add_node(ReasoningNode("N2", NodeType.CONSTRAINT, "Constraint", confidence=1.0))

        estimator = ConfidenceEstimator()
        score = estimator.calculate(graph)
        self.assertEqual(score, 1.0)

    def test_pipeline_execution_l2(self):
        result = self.pipeline.run("Implement user authentication with JWT", depth=ReasoningDepth.L2_STANDARD)
        self.assertIsInstance(result, ReasoningResult)
        self.assertTrue(result.is_approved)
        self.assertGreaterEqual(result.confidence_score, 0.70)
        self.assertGreater(result.metrics.node_count, 0)
        self.assertGreater(result.metrics.total_time_ms, 0.0)

    def test_pipeline_execution_l1_fast(self):
        result = self.pipeline.run("Fix typo in README", depth=ReasoningDepth.L1_FAST)
        self.assertEqual(result.plan.depth, ReasoningDepth.L1_FAST)
        self.assertTrue(result.is_approved)


if __name__ == '__main__':
    unittest.main()
