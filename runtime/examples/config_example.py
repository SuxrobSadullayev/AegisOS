"""
Module 1 Example: Aegis Configuration & Core Types Usage
"""

import sys
import os

# Add project root to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from runtime.src.config import (
    AegisConfig,
    ReasoningDepth,
    EpistemicState,
    EvidenceLevel,
    ClaimObject,
)


def main():
    print("=== Aegis ConfigManager Example ===")
    config = AegisConfig.load_from_env()
    print(f"Base Directory: {config.base_dir}")
    print(f"Gemini Model: {config.gemini_model}")
    print(f"Confidence Threshold: {config.confidence_threshold}")
    print(f"Max Retries: {config.max_retries}")
    print(f"Token Budget: {config.core_token_budget}")

    print("\n=== ClaimObject Data Structure Example ===")
    claim = ClaimObject(
        claim_id="CLM-000001",
        statement="PostgreSQL pool size 20 verified",
        state=EpistemicState.VERIFIED_FACT,
        evidence_level=EvidenceLevel.LEVEL_3_CODE_INSPECTION,
    )
    print(f"Claim ID: {claim.claim_id}")
    print(f"Statement: {claim.statement}")
    print(f"State: {claim.state.value}")
    print(f"Evidence Level: {claim.evidence_level.value}")
    print(f"Serialized Dictionary: {claim.to_dict()}")


if __name__ == "__main__":
    main()
