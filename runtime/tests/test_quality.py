import unittest
from runtime.src.config import AegisConfig, QualityStatus
from runtime.src.gateway import MockProvider
from runtime.src.quality import (
    QualityPipeline,
    QualityContext,
    QualityRule,
    QualitySeverity,
    QualityIssue,
    QualityResult,
    QualityReport,
    RepairResult,
    HallucinationValidator,
    PromptInjectionResidueValidator,
    FormattingValidator,
    IncompleteAnswerValidator,
    LowConfidenceValidator,
    ArchitectureViolationValidator
)


class TestQualityEngine(unittest.TestCase):
    def setUp(self):
        self.config = AegisConfig(max_retries=2)
        self.gateway = MockProvider(self.config)
        self.pipeline = QualityPipeline(self.config, self.gateway)

    def test_pass_validation(self):
        ctx = QualityContext(
            system_prompt="System",
            user_prompt="User",
            model_response_text="This is a valid Aegis production response that passes all gates cleanly.",
            config=self.config
        )
        report = self.pipeline.validate(ctx)
        self.assertEqual(report.result.status, QualityStatus.PASS)
        self.assertEqual(len(report.result.issues), 0)
        self.assertEqual(report.result.score, 1.0)
        self.assertGreater(report.metrics.validation_time_ms, 0.0)

    def test_prompt_injection_residue_detector(self):
        ctx = QualityContext(
            system_prompt="System",
            user_prompt="User",
            model_response_text="Here is the output with API_KEY='secret12345'",
            config=self.config
        )
        validator = PromptInjectionResidueValidator()
        issues = validator.validate(ctx)
        self.assertTrue(len(issues) > 0)
        self.assertEqual(issues[0].rule, QualityRule.PROMPT_INJECTION_RESIDUE)
        self.assertEqual(issues[0].severity, QualitySeverity.CRITICAL)

    def test_formatting_validator(self):
        ctx = QualityContext(
            system_prompt="System",
            user_prompt="User",
            model_response_text="Unclosed code block ``` python print('hello')",
            config=self.config
        )
        validator = FormattingValidator()
        issues = validator.validate(ctx)
        self.assertTrue(len(issues) > 0)
        self.assertEqual(issues[0].rule, QualityRule.FORMATTING)

    def test_incomplete_answer_validator(self):
        ctx = QualityContext(
            system_prompt="System",
            user_prompt="User",
            model_response_text="",
            config=self.config
        )
        validator = IncompleteAnswerValidator()
        issues = validator.validate(ctx)
        self.assertTrue(len(issues) > 0)
        self.assertEqual(issues[0].rule, QualityRule.INCOMPLETE_ANSWER)

    def test_architecture_violation_validator(self):
        ctx = QualityContext(
            system_prompt="System",
            user_prompt="User",
            model_response_text="result = eval(user_input)",
            config=self.config
        )
        validator = ArchitectureViolationValidator()
        issues = validator.validate(ctx)
        self.assertTrue(len(issues) > 0)
        self.assertEqual(issues[0].rule, QualityRule.ARCHITECTURE_VIOLATION)

    def test_auto_repair_loop_success(self):
        # Initial response has secret key, but MockProvider refinement will produce clean response
        initial_response = "Response containing API_KEY='secret123'"
        repair_res = self.pipeline.validate_and_refine("System", "User", initial_response)
        self.assertTrue(repair_res.is_repaired)
        self.assertGreater(repair_res.attempts_used, 0)
        self.assertNotIn("API_KEY", repair_res.repaired_text)


if __name__ == '__main__':
    unittest.main()
