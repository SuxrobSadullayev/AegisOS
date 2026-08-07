import unittest
import os
from runtime.src.config import AegisConfig, ReasoningDepth, EpistemicState, EvidenceLevel

class TestConfigManager(unittest.TestCase):
    def test_default_config_load(self):
        config = AegisConfig.load_from_env()
        self.assertIsNotNone(config.base_dir)
        self.assertEqual(config.max_retries, 3)
        self.assertEqual(config.confidence_threshold, 0.70)

    def test_enums(self):
        self.assertEqual(ReasoningDepth.L1_FAST.value, "L1")
        self.assertEqual(EpistemicState.VERIFIED_FACT.value, "VERIFIED_FACT")
        self.assertEqual(EvidenceLevel.LEVEL_5_EXECUTION.value, 5)

if __name__ == '__main__':
    unittest.main()
