import unittest
from runtime.src.config import AegisConfig, QualityStatus
from runtime.src.gateway import MockProvider
from runtime.src.quality import QualityPipeline

class TestQualityPipeline(unittest.TestCase):
    def setUp(self):
        self.config = AegisConfig(max_retries=2)
        self.gateway = MockProvider(self.config)
        self.pipeline = QualityPipeline(self.config, self.gateway)

    def test_pass_validation(self):
        resp = "This is a valid Aegis production response that passes all gates cleanly."
        result = self.pipeline.validate_and_refine("System", "User prompt", resp)
        self.assertEqual(result.status, QualityStatus.PASS)
        self.assertEqual(len(result.failed_gates), 0)
        self.assertEqual(result.retry_count, 0)

    def test_security_gate_fail_refinement(self):
        resp_with_secret = "Here is the result API_KEY=secret12345"
        result = self.pipeline.validate_and_refine("System", "User prompt", resp_with_secret)
        # Mock gateway response will be generated during refinement
        self.assertEqual(result.retry_count, 1)

if __name__ == '__main__':
    unittest.main()
