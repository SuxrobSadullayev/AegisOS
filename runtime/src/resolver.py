"""
Modul 4: ContextResolver & Task Intent
Inspects user prompt and target context to resolve domain modules and determine reasoning depth (L1/L2/L3).
"""

from dataclasses import dataclass, field
from typing import List, Set
from runtime.src.config import ReasoningDepth


@dataclass
class ResolvedContext:
    target_modules: List[str] = field(default_factory=list)
    reasoning_depth: ReasoningDepth = ReasoningDepth.L2_STANDARD


class ContextResolver:
    def __init__(self):
        self.keywords_map = {
            "python": "modules/domains/languages/python/standards.md",
            "typescript": "modules/domains/languages/typescript/standards.md",
            "rust": "modules/domains/languages/rust/standards.md",
            "c": "modules/domains/languages/c/standards.md",
            "cpp": "modules/domains/languages/cpp/standards.md",
            "c++": "modules/domains/languages/cpp/standards.md",
            "security": "modules/domains/engineering/security/standards.md",
            "testing": "modules/domains/engineering/testing/standards.md",
            "architecture": "modules/domains/engineering/architecture/standards.md",
        }

    def resolve(self, prompt_text: str) -> ResolvedContext:
        text_lower = prompt_text.lower()
        selected_modules: Set[str] = set()

        for kw, module_path in self.keywords_map.items():
            if kw in text_lower:
                selected_modules.add(module_path)

        # Determine Reasoning Depth Level
        depth = ReasoningDepth.L2_STANDARD
        if any(w in text_lower for w in ["architecture", "refactor", "security", "database", "redesign"]):
            depth = ReasoningDepth.L3_DEEP
        elif any(w in text_lower for w in ["typo", "rename", "format", "fix typo", "minor"]):
            depth = ReasoningDepth.L1_FAST

        return ResolvedContext(
            target_modules=sorted(list(selected_modules)),
            reasoning_depth=depth,
        )
