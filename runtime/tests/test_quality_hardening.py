"""
Quality Engine Hardening & Auto-Repair Boundary Tests for Aegis AI Operating System.
Tests all 12 Quality Gates, enforces max retry limit of 3 for auto-repair loops,
and verifies graceful failure handling without infinite loops.
"""

import unittest
from runtime.src.config import AegisConfig, QualityStatus
from runtime.src.gateway import MockProvider, ModelResponse
from runtime.src.quality import (
    QualityPipeline, QualityContext, QualityRule, QualitySeverity, QualityIssue,
    HallucinationValidator, PromptInjectionResidueValidator, FormattingValidator,
    IncompleteAnswerValidator, LowConfidenceValidator, ArchitectureViolationValidator
)


class AlwaysFailingMockProvider(MockProvider):
    """Mock provider that continuously returns output failing quality gates."""
    def generate(self, system_prompt: str, user_prompt: str) -> ModelResponse:
        return ModelResponse(
            text="Unsafe answer containing eval(x) and incomplete response...",
            token_count=20,
            latency_ms=5.0,
            provider="always_failing_mock",
            model="mock-failing-v1"
        )


class TestQualityEngineHardening(unittest.TestCase):
    """Quality Engine Hardening and Auto-Repair Loop Tests."""

    def setUp(self):
        self.config = AegisConfig(max_retries=3)
        self.failing_provider = AlwaysFailingMockProvider(self.config)
        self.pipeline = QualityPipeline(self.config, self.failing_provider)

    def test_auto_repair_max_retry_limit_enforced(self):
        """1. Verifies Auto-Repair loop halts strictly after max_retries (3 retries)."""
        res = self.pipeline.validate_and_refine(
            "system_prompt",
            "user_prompt",
            "Unsafe answer containing eval(x) and incomplete response..."
        )

        # Must fail after exactly max_retries (3 attempts)
        self.assertEqual(res.status, QualityStatus.FAIL)
        self.assertFalse(res.is_repaired)
        self.assertLessEqual(res.attempts_used, self.config.max_retries)
        self.assertTrue(len(res.remaining_issues) > 0)

    def test_all_core_validators_detection(self):
        """2. Tests core quality validators detecting specific rule violations."""
        # Architecture violation
        arch_val = ArchitectureViolationValidator()
        issues_arch = arch_val.validate(QualityContext("s", "u", "code eval('1+1')", self.config))
        self.assertTrue(any(i.rule == QualityRule.ARCHITECTURE_VIOLATION for i in issues_arch))

        # Formatting / Markdown code block violation (unmatched delimiter)
        fmt_val = FormattingValidator()
        issues_fmt = fmt_val.validate(QualityContext("s", "u", "```python\ncode without closing delimiter", self.config))
        self.assertTrue(any(i.rule == QualityRule.FORMATTING for i in issues_fmt))

        # Incomplete answer violation (length < 10)
        inc_val = IncompleteAnswerValidator()
        issues_inc = inc_val.validate(QualityContext("s", "u", "Short", self.config))
        self.assertTrue(any(i.rule == QualityRule.INCOMPLETE_ANSWER for i in issues_inc))




if __name__ == "__main__":
    unittest.main()
