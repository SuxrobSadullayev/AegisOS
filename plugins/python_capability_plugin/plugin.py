"""
Aegis AI OS — Python Capability Plugin
Provides real Python language validation, quality rules, and prompt contributions.
"""

import ast
import os
from typing import Dict, List, Any, Callable
from runtime.src.plugin import (
    AegisPlugin, PluginManifest, PluginContext, PluginHook,
    PluginPromptContribution, PluginDiscovery
)
from runtime.src.quality import QualityValidator, QualityContext, QualityIssue, QualityRule, QualitySeverity


class PythonASTQualityValidator:
    """Quality validator checking generated Python code blocks for syntax errors and unsafe nodes."""

    def validate(self, context: QualityContext) -> List[QualityIssue]:
        issues: List[QualityIssue] = []
        text = context.model_response_text
        if "```python" not in text:
            return issues

        # Extract python code blocks
        blocks = text.split("```python")
        for i, block in enumerate(blocks[1:], 1):
            code = block.split("```")[0].strip()
            if not code:
                continue
            try:
                tree = ast.parse(code)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("eval", "exec"):
                        issues.append(QualityIssue(
                            rule=QualityRule.ARCHITECTURE_VIOLATION,
                            severity=QualitySeverity.CRITICAL,
                            description=f"Python code block #{i} contains prohibited dynamic execution '{node.func.id}()'",
                            location=f"python_code_block_{i}"
                        ))
            except SyntaxError as e:
                issues.append(QualityIssue(
                    rule=QualityRule.FORMATTING,
                    severity=QualitySeverity.HIGH,
                    description=f"Python syntax error in code block #{i}: {e.msg} at line {e.lineno}",
                    location=f"python_code_block_{i}"
                ))

        return issues


class PythonCapabilityPlugin(AegisPlugin):
    """Real Python capability extension for Aegis Runtime."""

    def get_manifest(self) -> PluginManifest:
        manifest_path = os.path.join(os.path.dirname(__file__), "manifest.yaml")
        discovery = PluginDiscovery()
        manifest = discovery._parse_yaml_manifest(manifest_path)
        if manifest is None:
            raise RuntimeError(f"Failed to parse manifest at: {manifest_path}")
        return manifest

    def on_initialize(self, ctx: PluginContext) -> bool:
        return True

    def on_activate(self, ctx: PluginContext) -> bool:
        return True

    def get_capabilities(self) -> Dict[str, List[Any]]:
        return {
            "validators": [PythonASTQualityValidator()],
        }

    def get_hook_handlers(self) -> Dict[PluginHook, Callable[[Dict[str, Any]], Any]]:
        def before_intent_handler(context: Dict[str, Any]) -> None:
            ctx = context.get("context")
            if ctx and hasattr(ctx, "metadata"):
                meta = dict(ctx.metadata)
                meta["python_plugin_active"] = True

        return {
            PluginHook.BEFORE_INTENT: before_intent_handler,
        }

    def get_prompt_contributions(self) -> List[PluginPromptContribution]:
        return [
            PluginPromptContribution(
                plugin_id="aegis.capability.python",
                content=(
                    "## PYTHON CAPABILITY STANDARDS\n"
                    "- All Python code must be 100% typed (PEP 484).\n"
                    "- No raw `eval()` or `exec()` usage allowed.\n"
                    "- Prefer standard library modules over third-party dependencies.\n"
                ),
                section="language_standards",
                priority=10
            )
        ]
