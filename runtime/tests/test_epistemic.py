import unittest
from runtime.src.config import EpistemicState, EvidenceLevel
from runtime.src.epistemic import EpistemicGraphStore

class TestEpistemicStore(unittest.TestCase):
    def setUp(self):
        self.store = EpistemicGraphStore()

    def test_create_claims_and_ids(self):
        c1 = self.store.create_claim("Config file exists", EpistemicState.VERIFIED_FACT, EvidenceLevel.LEVEL_3_CODE_INSPECTION)
        c2 = self.store.create_claim("Pool size is 20", EpistemicState.INFERENCE, EvidenceLevel.LEVEL_2_DEDUCTION, depends_on=[c1.claim_id])
        self.assertEqual(c1.claim_id, "CLM-000001")
        self.assertEqual(c2.claim_id, "CLM-000002")

    def test_cascade_invalidation(self):
        c1 = self.store.create_claim("Config file exists", EpistemicState.VERIFIED_FACT, EvidenceLevel.LEVEL_3_CODE_INSPECTION)
        c2 = self.store.create_claim("Pool size is 20", EpistemicState.INFERENCE, EvidenceLevel.LEVEL_2_DEDUCTION, depends_on=[c1.claim_id])
        c3 = self.store.create_claim("High latency expected", EpistemicState.HYPOTHESIS, EvidenceLevel.LEVEL_1_PARAMETRIC, depends_on=[c2.claim_id])

        # Invalidate root claim c1
        affected = self.store.update_claim_state(c1.claim_id, EpistemicState.INVALIDATED)
        self.assertIn(c2.claim_id, affected)
        self.assertIn(c3.claim_id, affected)
        self.assertEqual(self.store.claims[c2.claim_id].state, EpistemicState.SUSPECT)
        self.assertEqual(self.store.claims[c3.claim_id].state, EpistemicState.SUSPECT)

if __name__ == '__main__':
    unittest.main()
