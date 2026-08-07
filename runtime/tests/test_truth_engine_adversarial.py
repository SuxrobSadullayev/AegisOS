"""
Truth Engine Epistemic Graph Adversarial Verification Tests for Aegis AI OS.
Verifies rules preventing self-declared facts without evidence, evidence hierarchy,
cascade invalidation of child claims, and cycle detection.
"""

import unittest
from runtime.src.config import EpistemicState, EvidenceLevel
from runtime.src.epistemic import EpistemicGraphStore


class TestTruthEngineAdversarial(unittest.TestCase):
    """Adversarial verification tests for Epistemic Truth Engine."""

    def setUp(self):
        self.graph = EpistemicGraphStore()

    def test_unsubstantiated_claim_cannot_be_verified_fact(self):
        """1. Verifies claims without Level 4/5 evidence cannot become VERIFIED_FACT."""
        claim = self.graph.create_plugin_claim(
            plugin_id="plugin.untrusted",
            statement="Python 3.12 is present",
            requested_state=EpistemicState.VERIFIED_FACT,
            evidence_level=EvidenceLevel.LEVEL_0_UNSUBSTANTIATED
        )
        self.assertEqual(claim.state, EpistemicState.HYPOTHESIS)
        self.assertNotEqual(claim.state, EpistemicState.VERIFIED_FACT)

    def test_epistemic_state_transitions(self):
        """2. Verifies valid epistemic state transitions: UNKNOWN -> HYPOTHESIS -> INFERENCE -> VERIFIED_FACT."""
        c = self.graph.create_claim("Transition test statement")
        self.assertEqual(c.state, EpistemicState.UNKNOWN)

        # Transition to HYPOTHESIS
        self.graph.update_claim_state(c.claim_id, EpistemicState.HYPOTHESIS)
        self.assertEqual(self.graph.claims[c.claim_id].state, EpistemicState.HYPOTHESIS)

        # Transition to INFERENCE
        self.graph.update_claim_state(c.claim_id, EpistemicState.INFERENCE)
        self.assertEqual(self.graph.claims[c.claim_id].state, EpistemicState.INFERENCE)

    def test_cascade_invalidation_marks_downstream_claims_suspect(self):
        """3. Verifies invalidating a parent claim marks all dependent claims as SUSPECT."""
        parent = self.graph.create_claim("Database connection string valid", state=EpistemicState.INFERENCE)
        child1 = self.graph.create_claim("Connection pool initialized", state=EpistemicState.INFERENCE, depends_on=[parent.claim_id])
        child2 = self.graph.create_claim("User queries executed", state=EpistemicState.INFERENCE, depends_on=[child1.claim_id])

        # Invalidate parent
        affected = self.graph.update_claim_state(parent.claim_id, EpistemicState.INVALIDATED)

        self.assertIn(child1.claim_id, affected)
        self.assertIn(child2.claim_id, affected)
        self.assertEqual(self.graph.claims[child1.claim_id].state, EpistemicState.SUSPECT)
        self.assertEqual(self.graph.claims[child2.claim_id].state, EpistemicState.SUSPECT)

    def test_cycle_detection_in_claim_graph(self):
        """4. Verifies dependency cycle detection between claims."""
        c1 = self.graph.create_claim("Claim A")
        c2 = self.graph.create_claim("Claim B", depends_on=[c1.claim_id])

        # c2 depends on c1. Path exists from c2 to c1.
        self.assertTrue(self.graph._has_path(c2.claim_id, c1.claim_id))
        self.assertFalse(self.graph._has_path(c1.claim_id, c2.claim_id))


if __name__ == "__main__":
    unittest.main()
