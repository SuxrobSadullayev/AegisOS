"""
Aegis AI OS — Security Capability Plugin
Provides real security quality gates (secret pattern detection, private key leaks) and security rules.
"""

import re
import os
from typing import Dict, List, Any, Callable
from runtime.src.plugin import (
    AegisPlugin, PluginManifest, PluginContext, PluginHook,
    PluginPromptContribution, PluginDiscovery
)
from runtime.src.quality import QualityValidator, QualityContext, QualityIssue, QualityRule, QualitySeverity


class SecuritySecretScannerValidator:
    """Quality validator inspecting response output for private keys and leaked tokens."""

    SECRET_PATTERNS = [
        (re.compile(r"-----BEGIN (?:[A-Z0-9_ ]+)?PRIVATE KEY-----"), "Private key header leak detected"),
        (re.compile(r"ghp_[A-Za-z0-9_]{36}"), "GitHub Personal Access Token leak detected"),
        (re.compile(r"sk-[A-Za-z0-9]{48}"), "API secret key leak detected"),
        (re.compile(r"xox[bap]-[A-Za-z0-9\-]+"), "Slack Token leak detected"),
    ]



    def validate(self, context: QualityContext) -> List[QualityIssue]:
        issues: List[QualityIssue] = []
        text = context.model_response_text

        for pattern, desc in self.SECRET_PATTERNS:
            if pattern.search(text):
                issues.append(QualityIssue(
                    rule=QualityRule.PROMPT_INJECTION_RESIDUE,
                    severity=QualitySeverity.CRITICAL,
                    description=desc,
                    location="payload"
                ))

        return issues


class SecurityCapabilityPlugin(AegisPlugin):
    """Real Security capability extension for Aegis Runtime."""

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
            "validators": [SecuritySecretScannerValidator()],
        }

    def get_hook_handlers(self) -> Dict[PluginHook, Callable[[Dict[str, Any]], Any]]:
        def before_quality_handler(context: Dict[str, Any]) -> None:
            ctx = context.get("context")
            if ctx and hasattr(ctx, "metadata"):
                meta = dict(ctx.metadata)
                meta["security_scan_completed"] = True

        return {
            PluginHook.BEFORE_QUALITY: before_quality_handler,
        }

    def get_prompt_contributions(self) -> List[PluginPromptContribution]:
        return [
            PluginPromptContribution(
                plugin_id="aegis.capability.security",
                content=(
                    "## SECURITY MANDATES\n"
                    "- Never hardcode credentials, tokens, or private key strings in code outputs.\n"
                    "- Always validate input boundaries and sanitize SQL/shell commands.\n"
                    "- Enforce principle of least privilege on all system boundaries.\n"
                ),
                section="security_mandates",
                priority=5
            )
        ]
