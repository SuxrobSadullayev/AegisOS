# Aegis Runtime Core Module 1: ConfigManager & Core Types

## Purpose

The `config` module provides centralized configuration management and core domain types for the Aegis AI Operating System runtime.

## Public API

- `AegisConfig`: Central configuration class with environment loading (`load_from_env()`), validation (`validate()`), and dictionary serialization (`to_dict()`).
- `ClaimObject`: Data structure representing internal claims (`claim_id`, `statement`, `state`, `evidence_level`, `depends_on_claim_ids`).
- Enums:
  - `ReasoningDepth` (`L1_FAST`, `L2_STANDARD`, `L3_DEEP`)
  - `EpistemicState` (`UNKNOWN`, `HYPOTHESIS`, `INFERENCE`, `VERIFIED_FACT`, `INVALIDATED`, `SUSPECT`)
  - `EvidenceLevel` (Levels 0 through 5)
  - `QualityStatus` (`PASS`, `FAIL`)

## Usage Example

See `runtime/examples/config_example.py`.
