"""
Modul 6: PromptComposer & Token Windowing
Combines Layer 0 Core files, Layer 1 Domain Modules, and Engine Pipeline Traces into a structured System Prompt Payload.
"""

from typing import Dict
from runtime.src.config import AegisConfig
from runtime.src.loaders import KernelLoader, KnowledgeLoader
from runtime.src.resolver import ResolvedContext
from runtime.src.pipeline import EnginePipelineTrace


class PromptComposer:
    def __init__(self, config: AegisConfig):
        self.config = config
        self.kernel_loader = KernelLoader(config)
        self.knowledge_loader = KnowledgeLoader(config)

    def compose(self, resolved_ctx: ResolvedContext, trace: EnginePipelineTrace) -> str:
        parts = []

        # 1. Layer 0 Core Kernel
        core_files = self.kernel_loader.load_core_files()
        parts.append("# LAYER 0: AEGIS KERNEL CONTEXT\n")
        for rel_path, content in core_files.items():
            parts.append(f"<!-- File: {rel_path} -->\n{content}\n")

        # 2. Engine Pipeline Trace Header
        parts.append("\n# RUNTIME ENGINE TRACE\n")
        parts.append(f"- Reasoning Depth: {trace.depth.value}")
        parts.append(f"- Confidence Score: {trace.confidence_score:.2f}")
        parts.append(f"- Executed Steps: {', '.join(trace.steps_executed)}")
        parts.append(f"- Gate Status: {'PASS' if trace.gate_passed else 'FAIL'}\n")

        # 3. Layer 1 Domain Modules
        if resolved_ctx.target_modules:
            parts.append("\n# LAYER 1: DOMAIN MODULES\n")
            for mod_path in resolved_ctx.target_modules:
                mod_content = self.knowledge_loader.load_module(mod_path)
                if mod_content:
                    parts.append(f"<!-- Module: {mod_path} -->\n{mod_content}\n")

        return "\n".join(parts)
