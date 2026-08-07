"""
Aegis AI Operating System — Module 1: ConfigManager & Core Types
Provides environment configuration, type-safe data structures, and core domain enums.
"""

import os
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, List, Optional, Any


class ReasoningDepth(Enum):
    """Reasoning depth levels for analytical processing."""
    L1_FAST = "L1"
    L2_STANDARD = "L2"
    L3_DEEP = "L3"


class EpistemicState(Enum):
    """Internal claim states managed by Truth Engine State Machine."""
    UNKNOWN = "UNKNOWN"
    HYPOTHESIS = "HYPOTHESIS"
    INFERENCE = "INFERENCE"
    VERIFIED_FACT = "VERIFIED_FACT"
    INVALIDATED = "INVALIDATED"
    SUSPECT = "SUSPECT"


class EvidenceLevel(Enum):
    """Evidence hierarchy levels (0 to 5) for verification requirements."""
    LEVEL_0_UNSUBSTANTIATED = 0
    LEVEL_1_PARAMETRIC = 1
    LEVEL_2_DEDUCTION = 2
    LEVEL_3_CODE_INSPECTION = 3
    LEVEL_4_SPECIFICATION = 4
    LEVEL_5_EXECUTION = 5


class QualityStatus(Enum):
    """Quality Engine gate evaluation status."""
    PASS = "PASS"
    FAIL = "FAIL"


@dataclass
class ClaimObject:
    """Canonical Claim Identity Data Structure."""
    claim_id: str
    statement: str
    state: EpistemicState = EpistemicState.UNKNOWN
    evidence_level: EvidenceLevel = EvidenceLevel.LEVEL_0_UNSUBSTANTIATED
    evidence_refs: List[str] = field(default_factory=list)
    depends_on_claim_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["state"] = self.state.value
        data["evidence_level"] = self.evidence_level.value
        return data


@dataclass
class AegisConfig:
    """Central Aegis Runtime Configuration Management."""
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-pro"
    max_retries: int = 3
    confidence_threshold: float = 0.70
    core_token_budget: int = 4000
    debug_mode: bool = False
    base_dir: str = ""

    @classmethod
    def load_from_env(cls) -> "AegisConfig":
        """Loads configuration from environment variables with sensible defaults."""
        base_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..")
        )
        config = cls(
            gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
            gemini_model=os.getenv("GEMINI_MODEL", "gemini-1.5-pro"),
            max_retries=int(os.getenv("AEGIS_MAX_RETRIES", "3")),
            confidence_threshold=float(os.getenv("AEGIS_CONFIDENCE_THRESHOLD", "0.70")),
            core_token_budget=int(os.getenv("AEGIS_CORE_TOKEN_BUDGET", "4000")),
            debug_mode=os.getenv("AEGIS_DEBUG", "0").lower() in ("1", "true", "yes"),
            base_dir=base_dir,
        )
        config.validate()
        return config

    def validate(self) -> bool:
        """Validates configuration parameters for correctness."""
        if not (0.0 <= self.confidence_threshold <= 1.0):
            raise ValueError(
                f"Invalid confidence_threshold: {self.confidence_threshold}. Must be between 0.0 and 1.0"
            )
        if self.max_retries < 0:
            raise ValueError(
                f"Invalid max_retries: {self.max_retries}. Must be non-negative"
            )
        if self.core_token_budget <= 0:
            raise ValueError(
                f"Invalid core_token_budget: {self.core_token_budget}. Must be positive"
            )
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Converts configuration object into a serializable dictionary."""
        return asdict(self)
