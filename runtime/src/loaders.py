"""
Modul 2: KernelLoader & KnowledgeLoader
Loads static Layer 0 Core files and Layer 1 Domain Modules from disk into memory.
"""

import os
from typing import Dict, List, Optional
from runtime.src.config import AegisConfig


class KernelLoader:
    def __init__(self, config: AegisConfig):
        self.config = config

    def load_core_files(self) -> Dict[str, str]:
        core_files = [
            "core/kernel/constitution.md",
            "core/engines/truth-engine.md",
            "core/engines/reasoning-engine.md",
            "core/engines/quality-engine.md",
            "core/workflow/workflow.md",
            "core/contracts/module.md",
        ]
        loaded = {}
        for rel_path in core_files:
            full_path = os.path.join(self.config.base_dir, rel_path)
            if os.path.exists(full_path):
                with open(full_path, "r", encoding="utf-8") as f:
                    loaded[rel_path] = f.read()
            else:
                raise FileNotFoundError(f"Required Kernel file missing: {rel_path}")
        return loaded

    def calculate_core_tokens(self, core_contents: Dict[str, str]) -> int:
        total_words = sum(len(content.split()) for content in core_contents.values())
        return int(total_words * 1.3)


class KnowledgeLoader:
    def __init__(self, config: AegisConfig):
        self.config = config

    def load_module(self, rel_path: str) -> Optional[str]:
        full_path = os.path.join(self.config.base_dir, rel_path)
        if os.path.exists(full_path):
            with open(full_path, "r", encoding="utf-8") as f:
                return f.read()
        return None
