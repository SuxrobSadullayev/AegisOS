"""
Modul 8: QualityPipeline & Auto-Refinement Loop
Evaluates model response against Quality Engine rules and executes iterative feedback refinement loops (max 3 retries).
"""

from dataclasses import dataclass
from typing import List, Tuple
from runtime.src.config import AegisConfig, QualityStatus
from runtime.src.gateway import ModelGatewayInterface


@dataclass
class QualityValidationResult:
    status: QualityStatus
    failed_gates: List[str]
    refined_response: str
    retry_count: int


class QualityPipeline:
    def __init__(self, config: AegisConfig, model_gateway: ModelGatewayInterface):
        self.config = config
        self.gateway = model_gateway

    def validate_and_refine(
        self, system_prompt: str, user_prompt: str, initial_response: str
    ) -> QualityValidationResult:
        curr_response = initial_response
        retries = 0

        while retries <= self.config.max_retries:
            status, failed_gates = self._evaluate_gates(curr_response)
            if status == QualityStatus.PASS or retries == self.config.max_retries:
                return QualityValidationResult(
                    status=status,
                    failed_gates=failed_gates,
                    refined_response=curr_response,
                    retry_count=retries,
                )

            # Auto-refinement loop: send Delta Feedback Prompt
            retries += 1
            feedback_prompt = (
                f"{user_prompt}\n\n"
                f"[AEGIS QUALITY ENGINE FEEDBACK — RETRY #{retries}]\n"
                f"Your previous output failed the following Quality Gates: {', '.join(failed_gates)}.\n"
                f"Please refine your solution to strictly pass all Quality Gates."
            )
            curr_response_obj = self.gateway.generate(system_prompt, feedback_prompt)
            curr_response = curr_response_obj.text if hasattr(curr_response_obj, 'text') else str(curr_response_obj)

        return QualityValidationResult(
            status=QualityStatus.FAIL,
            failed_gates=failed_gates,
            refined_response=curr_response,
            retry_count=retries,
        )

    def _evaluate_gates(self, response: str) -> Tuple[QualityStatus, List[str]]:
        failed = []

        # Gate 2: Security check (No exposed secrets)
        if any(secret in response for secret in ["API_KEY=", "SECRET_KEY=", "PASSWORD="]):
            failed.append("SecurityReview")

        # Gate 5: Readability check (Non-empty, valid text)
        if not response or len(response.strip()) < 10:
            failed.append("ReadabilityReview")

        # Gate 8: Consistency check (No error headers)
        if "HTTPError" in response or "Error connecting" in response:
            failed.append("ConsistencyReview")

        if failed:
            return QualityStatus.FAIL, failed
        return QualityStatus.PASS, []
