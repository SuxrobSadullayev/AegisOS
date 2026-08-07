import unittest
import os
from runtime.src.config import (
    AegisConfig,
    ReasoningDepth,
    EpistemicState,
    EvidenceLevel,
    QualityStatus,
    ClaimObject,
)


class TestConfigManager(unittest.TestCase):
    def test_default_config_load(self):
        config = AegisConfig.load_from_env()
        self.assertTrue(os.path.isabs(config.base_dir))
        self.assertEqual(config.max_retries, 3)
        self.assertEqual(config.confidence_threshold, 0.70)
        self.assertEqual(config.core_token_budget, 4000)
        self.assertTrue(config.validate())

    def test_to_dict_serialization(self):
        config = AegisConfig(gemini_model="gemini-1.5-flash", max_retries=5)
        d = config.to_dict()
        self.assertEqual(d["gemini_model"], "gemini-1.5-flash")
        self.assertEqual(d["max_retries"], 5)

    def test_validation_errors(self):
        with self.assertRaises(ValueError):
            AegisConfig(confidence_threshold=1.5).validate()

        with self.assertRaises(ValueError):
            AegisConfig(confidence_threshold=-0.1).validate()

        with self.assertRaises(ValueError):
            AegisConfig(max_retries=-1).validate()

        with self.assertRaises(ValueError):
            AegisConfig(core_token_budget=0).validate()

    def test_enums(self):
        self.assertEqual(ReasoningDepth.L1_FAST.value, "L1")
        self.assertEqual(ReasoningDepth.L2_STANDARD.value, "L2")
        self.assertEqual(ReasoningDepth.L3_DEEP.value, "L3")
        self.assertEqual(EpistemicState.VERIFIED_FACT.value, "VERIFIED_FACT")
        self.assertEqual(EvidenceLevel.LEVEL_5_EXECUTION.value, 5)
        self.assertEqual(QualityStatus.PASS.value, "PASS")

    def test_claim_object_serialization(self):
        claim = ClaimObject(
            claim_id="CLM-000001",
            statement="Test statement",
            state=EpistemicState.INFERENCE,
            evidence_level=EvidenceLevel.LEVEL_2_DEDUCTION,
            depends_on_claim_ids=["CLM-000000"],
        )
        d = claim.to_dict()
        self.assertEqual(d["claim_id"], "CLM-000001")
        self.assertEqual(d["state"], "INFERENCE")
        self.assertEqual(d["evidence_level"], 2)
        self.assertEqual(d["depends_on_claim_ids"], ["CLM-000000"])


if __name__ == "__main__":
    unittest.main()
