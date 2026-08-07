import unittest
from runtime.src.config import AegisConfig, QualityStatus
from runtime.src.gateway import MockProvider
from runtime.src.quality import QualityPipeline, QualityContext


class TestQualityIntegration(unittest.TestCase):
    def setUp(self):
        self.config = AegisConfig(max_retries=1)
        self.failing_gateway = MockProvider(self.config, simulate_error=True)

    def test_pipeline_unrepaired_failure_handling(self):
        # Create pipeline with failing gateway where retries will fail
        pipeline = QualityPipeline(self.config, self.failing_gateway)
        initial = "API_KEY='leaked_key'"
        
        with self.assertRaises(RuntimeError):
            pipeline.validate_and_refine("System", "User", initial)

    def test_full_quality_pipeline_validation_run(self):
        gateway = MockProvider(self.config)
        pipeline = QualityPipeline(self.config, gateway)
        ctx = QualityContext(
            system_prompt="Execute kernel standards",
            user_prompt="Refactor auth module",
            model_response_text="```python\ndef refactor():\n    pass\n```",
            config=self.config,
            confidence_score=0.85
        )
        report = pipeline.validate(ctx)
        self.assertEqual(report.result.status, QualityStatus.PASS)
        self.assertEqual(report.metrics.issues_found_count, 0)


if __name__ == '__main__':
    unittest.main()
