"""
Modul 5: EnginePipeline Coordinator
Orchestrates Truth Engine, Reasoning Engine, and Workflow Engine traces, enforcing confidence threshold gates.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any
from runtime.src.config import AegisConfig, EpistemicState, EvidenceLevel, ReasoningDepth
from runtime.src.epistemic import EpistemicGraphStore
from runtime.src.resolver import ResolvedContext


@dataclass
class EnginePipelineTrace:
    depth: ReasoningDepth
    steps_executed: List[str]
    confidence_score: float
    claims_verified: List[str]
    gate_passed: bool


class EnginePipeline:
    def __init__(self, config: AegisConfig, graph_store: EpistemicGraphStore):
        self.config = config
        self.graph_store = graph_store

    def execute(self, user_prompt: str, resolved_ctx: ResolvedContext) -> EnginePipelineTrace:
        depth = resolved_ctx.reasoning_depth
        steps = []

        if depth == ReasoningDepth.L1_FAST:
            steps = ["Decomposition", "Planning", "SelfVerification"]
        elif depth == ReasoningDepth.L2_STANDARD:
            steps = ["Decomposition", "Planning", "TradeOffAnalysis", "RiskAnalysis", "EvidenceGathering", "ConfidenceEstimation", "SelfVerification"]
        else:
            steps = [
                "Decomposition", "Planning", "TradeOffAnalysis", "RiskAnalysis",
                "Alternatives", "DecisionCriteria", "EvidenceGathering",
                "ConfidenceEstimation", "SelfVerification"
            ]

        # Calculate confidence score based on epistemic claim graph
        confidence = self._calculate_confidence()
        gate_passed = confidence >= self.config.confidence_threshold

        claims_verified = [
            claim_id for claim_id, claim in self.graph_store.claims.items()
            if claim.state == EpistemicState.VERIFIED_FACT
        ]

        return EnginePipelineTrace(
            depth=depth,
            steps_executed=steps,
            confidence_score=confidence,
            claims_verified=claims_verified,
            gate_passed=gate_passed,
        )

    def _calculate_confidence(self) -> float:
        claims = self.graph_store.claims
        if not claims:
            return 0.85  # Baseline default when no unverified hypotheses exist

        total_weight = 0.0
        sum_scores = 0.0

        for claim in claims.values():
            weight = 1.0
            if claim.state == EpistemicState.VERIFIED_FACT:
                score = 1.0
            elif claim.state == EpistemicState.INFERENCE:
                score = 0.80
            elif claim.state == EpistemicState.HYPOTHESIS:
                score = 0.50
            elif claim.state == EpistemicState.SUSPECT:
                score = 0.30
            else:  # INVALIDATED / UNKNOWN
                score = 0.0

            total_weight += weight
            sum_scores += score * weight

        return round(sum_scores / total_weight, 2)
