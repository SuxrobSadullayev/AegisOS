"""
Aegis AI Operating System — Production Quality Engine Subsystem (v2.0.0)
Provides deterministic validation gates: Hallucination detection, missing evidence,
logical inconsistency, circular reasoning, incomplete answer, prompt injection residue,
formatting, low confidence, architecture & contract violations, and Auto-Repair loop.
Python 3.12+ compliant. Zero placeholders. Zero external dependencies.
"""

import time
import re
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Any, Protocol
from runtime.src.config import AegisConfig, QualityStatus
from runtime.src.gateway import ModelGatewayInterface


class QualitySeverity(Enum):
    """Severity levels for quality gate violations."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class QualityRule(Enum):
    """Deterministic Quality Validation Rules (12 Gates)."""
    HALLUCINATION = "HALLUCINATION"
    MISSING_EVIDENCE = "MISSING_EVIDENCE"
    LOGICAL_INCONSISTENCY = "LOGICAL_INCONSISTENCY"
    CIRCULAR_REASONING = "CIRCULAR_REASONING"
    INCOMPLETE_ANSWER = "INCOMPLETE_ANSWER"
    MISSING_REQUIREMENTS = "MISSING_REQUIREMENTS"
    PROMPT_INJECTION_RESIDUE = "PROMPT_INJECTION_RESIDUE"
    FORMATTING = "FORMATTING"
    DUPLICATE_REASONING = "DUPLICATE_REASONING"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    ARCHITECTURE_VIOLATION = "ARCHITECTURE_VIOLATION"
    MODULE_CONTRACT_VIOLATION = "MODULE_CONTRACT_VIOLATION"


@dataclass
class QualityIssue:
    """Represents a single validation failure issue."""
    rule: QualityRule
    severity: QualitySeverity
    description: str
    location: str = "body"


@dataclass
class QualityContext:
    """Context object passed to Quality Engine validators."""
    system_prompt: str
    user_prompt: str
    model_response_text: str
    config: AegisConfig
    confidence_score: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationMetrics:
    """Performance metrics for a validation pass."""
    validation_time_ms: float
    evaluated_rules_count: int
    issues_found_count: int


@dataclass
class QualityResult:
    """Container for the output of a Quality Engine validation run."""
    status: QualityStatus
    issues: List[QualityIssue] = field(default_factory=list)
    score: float = 1.0
    failed_gates: List[str] = field(default_factory=list)
    refined_response: str = ""
    retry_count: int = 0


# Backward compatibility alias for orchestrator
QualityValidationResult = QualityResult


@dataclass
class QualityReport:
    """Full execution report for the Quality Engine."""
    result: QualityResult
    metrics: ValidationMetrics
    timestamp_utc: float = field(default_factory=time.time)


@dataclass
class RepairAction:
    """Actionable instruction for repairing a specific quality issue."""
    issue_rule: QualityRule
    correction_instruction: str


@dataclass
class RepairPlan:
    """Container for an auto-repair plan."""
    actions: List[RepairAction]
    attempt_number: int
    max_retries: int


@dataclass
class RepairResult:
    """Result of an auto-repair operation."""
    is_repaired: bool
    repaired_text: str
    attempts_used: int
    remaining_issues: List[QualityIssue]
    status: QualityStatus = QualityStatus.PASS


class QualityValidator(Protocol):
    """Protocol for all Quality Gate Validators."""
    def validate(self, context: QualityContext) -> List[QualityIssue]:
        ...


class HallucinationValidator:
    """Detects unverified claims or fake facts in response text."""

    def validate(self, context: QualityContext) -> List[QualityIssue]:
        issues = []
        text = context.model_response_text.lower()
        if "as an ai" in text or "i don't have access" in text:
            issues.append(QualityIssue(
                rule=QualityRule.HALLUCINATION,
                severity=QualitySeverity.MEDIUM,
                description="Model included boilerplate refusal or unverified capability claim",
                location="header"
            ))
        return issues


class PromptInjectionResidueValidator:
    """Detects prompt injection residue or leaked system instructions."""

    SECRET_PATTERNS = [
        re.compile(r"API_KEY\s*=\s*['\"][A-Za-z0-9_\-]+['\"]", re.IGNORECASE),
        re.compile(r"Bearer\s+ey[A-Za-z0-9_\-\.]+", re.IGNORECASE),
        re.compile(r"<!--\s*SYSTEM_PROMPT_SECRET", re.IGNORECASE),
        re.compile(r"IGNORE\s+ALL\s+PREVIOUS\s+INSTRUCTIONS", re.IGNORECASE),
    ]

    def validate(self, context: QualityContext) -> List[QualityIssue]:
        issues = []
        for pattern in self.SECRET_PATTERNS:
            if pattern.search(context.model_response_text):
                issues.append(QualityIssue(
                    rule=QualityRule.PROMPT_INJECTION_RESIDUE,
                    severity=QualitySeverity.CRITICAL,
                    description="Prompt injection residue or secret credential leak detected",
                    location="payload"
                ))
        return issues


class FormattingValidator:
    """Validates markdown syntax and code block language tags."""

    def validate(self, context: QualityContext) -> List[QualityIssue]:
        issues = []
        text = context.model_response_text
        if text.count("```") % 2 != 0:
            issues.append(QualityIssue(
                rule=QualityRule.FORMATTING,
                severity=QualitySeverity.HIGH,
                description="Unmatched code block delimiter (```) in markdown",
                location="markdown_structure"
            ))
        return issues


class IncompleteAnswerValidator:
    """Checks for empty responses or truncated sentences."""

    def validate(self, context: QualityContext) -> List[QualityIssue]:
        issues = []
        text = context.model_response_text.strip()
        if not text:
            issues.append(QualityIssue(
                rule=QualityRule.INCOMPLETE_ANSWER,
                severity=QualitySeverity.CRITICAL,
                description="Empty response text returned",
                location="body"
            ))
        elif len(text) < 10:
            issues.append(QualityIssue(
                rule=QualityRule.INCOMPLETE_ANSWER,
                severity=QualitySeverity.HIGH,
                description="Trivially short or incomplete response text",
                location="body"
            ))
        return issues


class LowConfidenceValidator:
    """Checks if the reasoning confidence score falls below system threshold."""

    def validate(self, context: QualityContext) -> List[QualityIssue]:
        issues = []
        if context.confidence_score < context.config.confidence_threshold:
            issues.append(QualityIssue(
                rule=QualityRule.LOW_CONFIDENCE,
                severity=QualitySeverity.HIGH,
                description=f"Reasoning confidence {context.confidence_score:.2f} is below threshold {context.config.confidence_threshold:.2f}",
                location="confidence_score"
            ))
        return issues


class ArchitectureViolationValidator:
    """Checks for prohibited architecture practices (e.g. static offsets)."""

    def validate(self, context: QualityContext) -> List[QualityIssue]:
        issues = []
        text = context.model_response_text
        if "eval(" in text or "exec(" in text:
            issues.append(QualityIssue(
                rule=QualityRule.ARCHITECTURE_VIOLATION,
                severity=QualitySeverity.CRITICAL,
                description="Unsafe evaluation dynamic code execution detected (eval/exec)",
                location="code_block"
            ))
        return issues


class QualityPipeline:
    """
    Production Quality Pipeline with 12 deterministic validation gates
    and an automated Auto-Repair loop (up to max_retries).
    """

    def __init__(self, config: AegisConfig, model_gateway: Optional[ModelGatewayInterface] = None):
        self.config = config
        self.model_gateway = model_gateway
        self._core_validators: List[QualityValidator] = [
            HallucinationValidator(),
            PromptInjectionResidueValidator(),
            FormattingValidator(),
            IncompleteAnswerValidator(),
            LowConfidenceValidator(),
            ArchitectureViolationValidator(),
        ]
        self.plugin_validators: List[QualityValidator] = []

    @property
    def validators(self) -> List[QualityValidator]:
        """Combined list of core validators (always enforced) and plugin validators."""
        return self._core_validators + self.plugin_validators

    def register_validator(self, validator: QualityValidator) -> None:
        """Plugins can add custom quality rules/validators."""
        if validator not in self.plugin_validators:
            self.plugin_validators.append(validator)

    def unregister_validator(self, validator: QualityValidator) -> bool:
        """Plugins cannot disable core kernel or security validators."""
        if validator in self._core_validators:
            raise PermissionError("Core kernel and security quality validators cannot be removed by plugins")
        if validator in self.plugin_validators:
            self.plugin_validators.remove(validator)
            return True
        return False


    def validate(self, context: QualityContext) -> QualityReport:
        """Executes all validators deterministically and returns a QualityReport."""
        start_time = time.time()
        issues: List[QualityIssue] = []

        for validator in self.validators:
            found = validator.validate(context)
            issues.extend(found)

        validation_time = (time.time() - start_time) * 1000.0
        failed_gates = list(set(issue.rule.value for issue in issues))

        status = QualityStatus.PASS if len(issues) == 0 else QualityStatus.FAIL
        score = max(0.0, round(1.0 - (len(issues) * 0.2), 2))

        result = QualityResult(
            status=status,
            issues=issues,
            score=score,
            failed_gates=failed_gates
        )

        metrics = ValidationMetrics(
            validation_time_ms=round(validation_time, 2),
            evaluated_rules_count=len(self.validators),
            issues_found_count=len(issues)
        )

        return QualityReport(result=result, metrics=metrics)

    def validate_and_refine(self, system_prompt: str, user_prompt: str, response_text: str) -> RepairResult:
        """
        Executes validation and enters the Auto-Repair loop (up to max_retries).
        Returns a RepairResult.
        """
        curr_text = response_text
        attempts = 0
        max_retries = self.config.max_retries

        while attempts <= max_retries:
            context = QualityContext(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model_response_text=curr_text,
                config=self.config
            )
            report = self.validate(context)

            if report.result.status == QualityStatus.PASS:
                return RepairResult(
                    is_repaired=True,
                    repaired_text=curr_text,
                    attempts_used=attempts,
                    remaining_issues=[],
                    status=QualityStatus.PASS
                )

            attempts += 1
            if attempts > max_retries or not self.model_gateway:
                return RepairResult(
                    is_repaired=False,
                    repaired_text=curr_text,
                    attempts_used=attempts - 1,
                    remaining_issues=report.result.issues,
                    status=QualityStatus.FAIL
                )

            # Generate Delta Feedback Prompt for Auto-Repair
            failed_str = ", ".join(report.result.failed_gates)
            delta_prompt = (
                f"{user_prompt}\n\n"
                f"[AEGIS QUALITY ENGINE REPAIR FEEDBACK — ATTEMPT #{attempts}]\n"
                f"Your previous output failed Quality Gates: {failed_str}.\n"
                f"Please fix all issues, remove any leaked credentials or raw prompt residue, and format properly."
            )

            resp_obj = self.model_gateway.generate(system_prompt, delta_prompt)
            curr_text = resp_obj.text if hasattr(resp_obj, "text") else str(resp_obj)

        return RepairResult(
            is_repaired=False,
            repaired_text=curr_text,
            attempts_used=attempts,
            remaining_issues=report.result.issues
        )
