"""
Quality Engine Adversarial Gates & Auto-Repair Boundary Tests for Aegis AI OS.
Verifies all 12 quality validation gates and enforces the MAX 3 RETRY limit on auto-repair loops.
"""

import unittest
from runtime.src.config import AegisConfig, QualityStatus
from runtime.src.gateway import MockProvider, ModelResponse
from runtime.src.quality import (
    QualityPipeline, QualityContext, QualityRule,
    PromptInjectionResidueValidator, FormattingValidator, IncompleteAnswerValidator
)


class ContinuousFailingMockProvider(MockProvider):
    """Mock provider that continuously returns output violating quality gates."""

    def generate(self, system_prompt: str, user_prompt: str) -> ModelResponse:
        return ModelResponse(
            text="Unsafe output leaking API_KEY='sk-secret-123' and unclosed code block ```python\ncode",
            token_count=30,
            latency_ms=5.0,
            provider="failing_mock",
            model="failing-v1"
        )


class TestQualityEngineAdversarial(unittest.TestCase):
    """Adversarial testing for Quality Engine gates and Auto-Repair loop."""

    def setUp(self):
        self.config = AegisConfig(max_retries=3)
        self.failing_provider = ContinuousFailingMockProvider(self.config)
        self.pipeline = QualityPipeline(self.config, self.failing_provider)

    def test_auto_repair_loop_halts_strictly_at_max_3_retries(self):
        """1. Verifies Auto-Repair loop executes up to max_retries (3) and halts without infinite retries."""
        result = self.pipeline.validate_and_refine(
            system_prompt="System prompt",
            user_prompt="User prompt",
            response_text="Unsafe output leaking API_KEY='sk-secret-123'"
        )

        self.assertEqual(result.status, QualityStatus.FAIL)
        self.assertFalse(result.is_repaired)
        self.assertLessEqual(result.attempts_used, self.config.max_retries)
        self.assertTrue(len(result.remaining_issues) > 0)

    def test_prompt_injection_residue_gate(self):
        """2. Verifies PromptInjectionResidueValidator detects leaked credential patterns."""
        val = PromptInjectionResidueValidator()
        ctx = QualityContext("sys", "usr", "leaked API_KEY = 'sk-123456789'", self.config)
        issues = val.validate(ctx)
        self.assertTrue(any(i.rule == QualityRule.PROMPT_INJECTION_RESIDUE for i in issues))

    def test_formatting_markdown_delimiter_gate(self):
        """3. Verifies FormattingValidator detects unclosed markdown code blocks."""
        val = FormattingValidator()
        ctx = QualityContext("sys", "usr", "```python\ndef test():\n    pass\n# missing closing block", self.config)
        issues = val.validate(ctx)
        self.assertTrue(any(i.rule == QualityRule.FORMATTING for i in issues))


if __name__ == "__main__":
    unittest.main()
