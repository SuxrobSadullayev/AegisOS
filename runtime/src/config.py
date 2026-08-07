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
    provider: str = "mock"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-pro"
    temperature: float = 0.7
    max_tokens: int = 4096
    reasoning_depth: str = "L2"
    max_retries: int = 3
    confidence_threshold: float = 0.70
    core_token_budget: int = 4000
    verbose: bool = False
    debug_mode: bool = False
    base_dir: str = ""
    enabled_plugins: List[str] = field(default_factory=list)

    @classmethod
    def load(cls, config_path: Optional[str] = None) -> "AegisConfig":
        """
        Loads configuration enforcing config precedence:
        CLI args (applied downstream) > Environment Variables > Config File (~/.aegis/config.yaml) > Defaults
        """
        base_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..")
        )
        config = cls(base_dir=base_dir)

        # 1. Try loading from config file if present
        target_path = config_path
        if not target_path:
            home_config = os.path.expanduser("~/.aegis/config.yaml")
            local_config = os.path.join(base_dir, ".aegis", "config.yaml")
            if os.path.isfile(home_config):
                target_path = home_config
            elif os.path.isfile(local_config):
                target_path = local_config

        if target_path and os.path.isfile(target_path):
            try:
                with open(target_path, "r", encoding="utf-8") as f:
                    file_data = cls._parse_simple_yaml(f.read())
                    config._apply_dict(file_data)
            except Exception as err:
                print(f"⚠️ Warning: Failed to parse config file '{target_path}': {err}")

        # 2. Override with Environment variables
        config._apply_env()
        config.validate()
        return config

    @classmethod
    def load_from_env(cls) -> "AegisConfig":
        """Alias for backward compatibility."""
        return cls.load()

    def _apply_env(self) -> None:
        """Applies environment variable overrides."""
        if os.getenv("AEGIS_PROVIDER"):
            self.provider = os.getenv("AEGIS_PROVIDER")
        if os.getenv("GEMINI_API_KEY"):
            self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        if os.getenv("GEMINI_MODEL"):
            self.gemini_model = os.getenv("GEMINI_MODEL")
        if os.getenv("AEGIS_MODEL"):
            self.gemini_model = os.getenv("AEGIS_MODEL")
        if os.getenv("AEGIS_TEMPERATURE"):
            self.temperature = float(os.getenv("AEGIS_TEMPERATURE"))
        if os.getenv("AEGIS_MAX_TOKENS"):
            self.max_tokens = int(os.getenv("AEGIS_MAX_TOKENS"))
        if os.getenv("AEGIS_REASONING_DEPTH"):
            self.reasoning_depth = os.getenv("AEGIS_REASONING_DEPTH")
        if os.getenv("AEGIS_MAX_RETRIES"):
            self.max_retries = int(os.getenv("AEGIS_MAX_RETRIES"))
        if os.getenv("AEGIS_CONFIDENCE_THRESHOLD"):
            self.confidence_threshold = float(os.getenv("AEGIS_CONFIDENCE_THRESHOLD"))
        if os.getenv("AEGIS_CORE_TOKEN_BUDGET"):
            self.core_token_budget = int(os.getenv("AEGIS_CORE_TOKEN_BUDGET"))
        if os.getenv("AEGIS_VERBOSE"):
            self.verbose = os.getenv("AEGIS_VERBOSE").lower() in ("1", "true", "yes")
        if os.getenv("AEGIS_DEBUG"):
            self.debug_mode = os.getenv("AEGIS_DEBUG").lower() in ("1", "true", "yes")

    def _apply_dict(self, data: Dict[str, Any]) -> None:
        """Applies dictionary key-value updates."""
        if "provider" in data:
            self.provider = str(data["provider"])
        if "gemini_model" in data or "model" in data:
            self.gemini_model = str(data.get("gemini_model") or data.get("model"))
        if "temperature" in data:
            self.temperature = float(data["temperature"])
        if "max_tokens" in data:
            self.max_tokens = int(data["max_tokens"])
        if "reasoning_depth" in data:
            self.reasoning_depth = str(data["reasoning_depth"])
        if "max_retries" in data:
            self.max_retries = int(data["max_retries"])
        if "confidence_threshold" in data:
            self.confidence_threshold = float(data["confidence_threshold"])
        if "core_token_budget" in data:
            self.core_token_budget = int(data["core_token_budget"])
        if "verbose" in data:
            self.verbose = bool(data["verbose"])
        if "debug_mode" in data or "debug" in data:
            self.debug_mode = bool(data.get("debug_mode") if "debug_mode" in data else data.get("debug"))
        if "enabled_plugins" in data and isinstance(data["enabled_plugins"], list):
            self.enabled_plugins = [str(x) for x in data["enabled_plugins"]]

    @staticmethod
    def _parse_simple_yaml(text: str) -> Dict[str, Any]:
        """Zero-dependency lightweight YAML parser for key-value pairs and simple lists."""
        result: Dict[str, Any] = {}
        current_list_key: Optional[str] = None

        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if line.startswith("- ") and current_list_key:
                val = line[2:].strip().strip('"').strip("'")
                if current_list_key not in result:
                    result[current_list_key] = []
                result[current_list_key].append(val)
                continue

            if ":" in line:
                key, val = line.split(":", 1)
                key = key.strip()
                val = val.strip()

                if not val:
                    current_list_key = key
                    result[key] = []
                    continue

                current_list_key = None
                # Strip quotes
                if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                    val = val[1:-1]

                # Convert booleans and numbers
                if val.lower() in ("true", "yes"):
                    result[key] = True
                elif val.lower() in ("false", "no"):
                    result[key] = False
                elif val.isdigit():
                    result[key] = int(val)
                else:
                    try:
                        result[key] = float(val)
                    except ValueError:
                        result[key] = val

        return result

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
        if not (0.0 <= self.temperature <= 2.0):
            raise ValueError(
                f"Invalid temperature: {self.temperature}. Must be between 0.0 and 2.0"
            )
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Converts configuration object into a serializable dictionary."""
        return asdict(self)
