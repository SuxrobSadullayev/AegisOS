"""
Truth Engine Security & Epistemic Verification Tests for Aegis AI Operating System.
Verifies epistemic state transitions, evidence level hierarchy (Level 0-5), prohibition
against self-declared VERIFIED_FACT claims without level 4/5 evidence, and cascade invalidation.
"""

import unittest
from runtime.src.config import EpistemicState, EvidenceLevel, ClaimObject
from runtime.src.epistemic import EpistemicGraphStore


class TestTruthEngineSecurity(unittest.TestCase):
    """Truth Engine Epistemic Graph Security Tests."""

    def setUp(self):
        self.graph = EpistemicGraphStore()

    def test_evidence_level_hierarchy_ordering(self):
        """1. Verifies EvidenceLevel hierarchy values: L0 < L1 < L2 < L3 < L4 < L5."""
        self.assertLess(EvidenceLevel.LEVEL_0_UNSUBSTANTIATED.value, EvidenceLevel.LEVEL_1_PARAMETRIC.value)
        self.assertLess(EvidenceLevel.LEVEL_1_PARAMETRIC.value, EvidenceLevel.LEVEL_2_DEDUCTION.value)
        self.assertLess(EvidenceLevel.LEVEL_2_DEDUCTION.value, EvidenceLevel.LEVEL_3_CODE_INSPECTION.value)
        self.assertLess(EvidenceLevel.LEVEL_3_CODE_INSPECTION.value, EvidenceLevel.LEVEL_4_SPECIFICATION.value)
        self.assertLess(EvidenceLevel.LEVEL_4_SPECIFICATION.value, EvidenceLevel.LEVEL_5_EXECUTION.value)

    def test_plugin_cannot_self_declare_verified_fact_without_level4_evidence(self):
        """2. Verifies Truth Engine rule: Plugins CANNOT promote claims to VERIFIED_FACT without Level 4/5 evidence."""
        # Level 0 evidence -> Demoted to HYPOTHESIS
        claim0 = self.graph.create_plugin_claim(
            plugin_id="plugin.untrusted",
            statement="Self-declared fact with Level 0 evidence",
            requested_state=EpistemicState.VERIFIED_FACT,
            evidence_level=EvidenceLevel.LEVEL_0_UNSUBSTANTIATED
        )
        self.assertEqual(claim0.state, EpistemicState.HYPOTHESIS)

        # Level 2 evidence -> Demoted to HYPOTHESIS
        claim2 = self.graph.create_plugin_claim(
            plugin_id="plugin.untrusted",
            statement="Self-declared fact with Level 2 evidence",
            requested_state=EpistemicState.VERIFIED_FACT,
            evidence_level=EvidenceLevel.LEVEL_2_DEDUCTION
        )
        self.assertEqual(claim2.state, EpistemicState.HYPOTHESIS)

        # Level 4 evidence -> Allowed as VERIFIED_FACT
        claim4 = self.graph.create_plugin_claim(
            plugin_id="plugin.trusted",
            statement="Fact backed by specification evidence",
            requested_state=EpistemicState.VERIFIED_FACT,
            evidence_level=EvidenceLevel.LEVEL_4_SPECIFICATION
        )
        self.assertEqual(claim4.state, EpistemicState.VERIFIED_FACT)

        # Level 5 evidence -> Allowed as VERIFIED_FACT
        claim5 = self.graph.create_plugin_claim(
            plugin_id="plugin.trusted",
            statement="Fact backed by execution evidence",
            requested_state=EpistemicState.VERIFIED_FACT,
            evidence_level=EvidenceLevel.LEVEL_5_EXECUTION
        )
        self.assertEqual(claim5.state, EpistemicState.VERIFIED_FACT)

    def test_cascade_invalidation_downstream_claims(self):
        """3. Verifies cascade invalidation: invalidating parent claim marks downstream claims as SUSPECT."""
        parent_claim = self.graph.create_claim(
            statement="Parent claim",
            state=EpistemicState.INFERENCE,
            evidence_level=EvidenceLevel.LEVEL_3_CODE_INSPECTION
        )

        child_claim = self.graph.create_claim(
            statement="Child claim depending on parent",
            state=EpistemicState.INFERENCE,
            evidence_level=EvidenceLevel.LEVEL_3_CODE_INSPECTION,
            depends_on=[parent_claim.claim_id]
        )

        grandchild_claim = self.graph.create_claim(
            statement="Grandchild claim depending on child",
            state=EpistemicState.INFERENCE,
            evidence_level=EvidenceLevel.LEVEL_3_CODE_INSPECTION,
            depends_on=[child_claim.claim_id]
        )

        # Invalidate parent claim
        affected = self.graph.update_claim_state(parent_claim.claim_id, EpistemicState.INVALIDATED)

        self.assertIn(child_claim.claim_id, affected)
        self.assertIn(grandchild_claim.claim_id, affected)
        self.assertEqual(self.graph.claims[child_claim.claim_id].state, EpistemicState.SUSPECT)
        self.assertEqual(self.graph.claims[grandchild_claim.claim_id].state, EpistemicState.SUSPECT)

    def test_circular_claim_dependency_prevention(self):
        """4. Verifies that circular dependencies between claims are detected via _has_path traversal."""
        c1 = self.graph.create_claim("Claim 1")
        c2 = self.graph.create_claim("Claim 2", depends_on=[c1.claim_id])

        # c2 depends on c1. Path from c2 to c1 exists.
        self.assertTrue(self.graph._has_path(c2.claim_id, c1.claim_id))
        self.assertFalse(self.graph._has_path(c1.claim_id, c2.claim_id))



if __name__ == "__main__":
    unittest.main()
