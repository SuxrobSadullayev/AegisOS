"""
Modul 1: ConfigManager & Core Types Definition
Handles environment configuration, system constants, and runtime core types.
"""

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any


class ReasoningDepth(Enum):
    L1_FAST = "L1"
    L2_STANDARD = "L2"
    L3_DEEP = "L3"


class EpistemicState(Enum):
    UNKNOWN = "UNKNOWN"
    HYPOTHESIS = "HYPOTHESIS"
    INFERENCE = "INFERENCE"
    VERIFIED_FACT = "VERIFIED_FACT"
    INVALIDATED = "INVALIDATED"
    SUSPECT = "SUSPECT"


class EvidenceLevel(Enum):
    LEVEL_0_UNSUBSTANTIATED = 0
    LEVEL_1_PARAMETRIC = 1
    LEVEL_2_DEDUCTION = 2
    LEVEL_3_CODE_INSPECTION = 3
    LEVEL_4_SPECIFICATION = 4
    LEVEL_5_EXECUTION = 5


class QualityStatus(Enum):
    PASS = "PASS"
    FAIL = "FAIL"


@dataclass
class ClaimObject:
    claim_id: str
    statement: str
    state: EpistemicState = EpistemicState.UNKNOWN
    evidence_level: EvidenceLevel = EvidenceLevel.LEVEL_0_UNSUBSTANTIATED
    evidence_refs: List[str] = field(default_factory=list)
    depends_on_claim_ids: List[str] = field(default_factory=list)


@dataclass
class AegisConfig:
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-pro"
    max_retries: int = 3
    confidence_threshold: float = 0.70
    core_token_budget: int = 4000
    debug_mode: bool = False
    base_dir: str = ""

    @classmethod
    def load_from_env(cls) -> "AegisConfig":
        base_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..")
        )
        return cls(
            gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
            gemini_model=os.getenv("GEMINI_MODEL", "gemini-1.5-pro"),
            max_retries=int(os.getenv("AEGIS_MAX_RETRIES", "3")),
            confidence_threshold=float(os.getenv("AEGIS_CONFIDENCE_THRESHOLD", "0.70")),
            debug_mode=os.getenv("AEGIS_DEBUG", "0").lower() in ("1", "true", "yes"),
            base_dir=base_dir,
        )
