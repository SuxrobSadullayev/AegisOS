"""
Integration tests for Aegis AI Operating System Plugin Subsystem (v2.0.0).
Provides 18+ comprehensive integration tests verifying subsystem collaboration:
Orchestrator, PromptComposer, TruthEngine, QualityEngine, SessionManager,
ModelGateway, SDK CLI, and real filesystem plugins.
"""

import os
import sys
import shutil
import tempfile
import unittest
from typing import Dict, List, Any
from runtime.src.config import AegisConfig, EpistemicState, EvidenceLevel, QualityStatus
from runtime.src.gateway import ModelGatewayFactory, ModelGatewayInterface, ModelResponse
from runtime.src.epistemic import EpistemicGraphStore
from runtime.src.loaders import KernelLoader
from runtime.src.resolver import ResolvedContext
from runtime.src.pipeline import EnginePipelineTrace, ReasoningDepth
from runtime.src.composer import PromptComposer
from runtime.src.quality import QualityPipeline, QualityContext, QualityIssue, QualityRule, QualitySeverity
from runtime.src.session import SessionManager, SessionContext
from runtime.src.orchestrator import RuntimeOrchestrator, OrchestratorContext, PipelineStage, StageResult, PipelineTracer
from runtime.src.plugin import (
    PluginManager, PluginManifest, PluginCapability, PluginPermission, PluginHook,
    PluginPromptContribution, AegisPlugin, PluginContext, CapabilityToken,
    PluginPermissionError, PluginDiscovery, ManifestValidator
)
from plugins.python_capability_plugin.plugin import PythonCapabilityPlugin
from plugins.security_capability_plugin.plugin import SecurityCapabilityPlugin


class CustomTestModelProvider(ModelGatewayInterface):
    """Custom model provider registered via plugin extension point."""
    def generate(self, system_prompt: str, user_prompt: str) -> ModelResponse:
        text = f"[Custom Plugin Provider Output] Response for prompt: {user_prompt}"
        return ModelResponse(
            text=text,
            token_count=self.estimate_tokens(text),
            latency_ms=5.0,
            provider="custom_plugin_provider",
            model="custom-v1"
        )

    def generate_stream(self, system_prompt: str, user_prompt: str):
        resp = self.generate(system_prompt, user_prompt)
        yield resp.text
        return resp


class TestPluginIntegration(unittest.TestCase):
    """18 Integration tests verifying end-to-end plugin architecture behavior."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="aegis_integration_test_")
        self.config = AegisConfig(base_dir=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
        self.plugins_dir = os.path.join(self.config.base_dir, "plugins")
        self.manager = PluginManager(self.plugins_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_discovery_real_plugins_directory(self):
        """1. Tests scanning and parsing real YAML manifests in plugins/ directory."""
        manifests = self.manager.discover_plugins()
        plugin_ids = [m.plugin_id for m in manifests]
        self.assertIn("aegis.capability.python", plugin_ids)
        self.assertIn("aegis.capability.security", plugin_ids)

    def test_multi_plugin_activation_and_collaboration(self):
        """2. Tests multi-plugin collaboration (Python + Security plugins active simultaneously)."""
        py_plugin = PythonCapabilityPlugin()
        sec_plugin = SecurityCapabilityPlugin()

        self.manager.register_builtin(py_plugin)
        self.manager.register_builtin(sec_plugin)

        activated = self.manager.activate_all({
            "aegis.capability.python": py_plugin,
            "aegis.capability.security": sec_plugin,
        })
        self.assertEqual(len(activated), 2)
        self.assertIn("aegis.capability.python", activated)
        self.assertIn("aegis.capability.security", activated)

    def test_prompt_composer_kernel_priority_over_plugins(self):
        """3. Tests PromptComposer: Layer 0 Kernel appears FIRST, plugin prompt contributions come after."""
        py_plugin = PythonCapabilityPlugin()
        self.manager.register_builtin(py_plugin)
        self.manager.activate_all({"aegis.capability.python": py_plugin})

        composer = PromptComposer(self.config)
        resolved_ctx = ResolvedContext()
        trace = EnginePipelineTrace(ReasoningDepth.L2_STANDARD, [], 0.90, [], True)

        contribs = self.manager.get_prompt_contributions()
        composed_prompt = composer.compose(resolved_ctx, trace, plugin_contributions=contribs)

        # Layer 0 Kernel context must be at top
        layer0_idx = composed_prompt.find("# LAYER 0: AEGIS KERNEL CONTEXT")
        layer2_idx = composed_prompt.find("# LAYER 2: PLUGIN EXTENSIONS")

        self.assertNotEqual(layer0_idx, -1)
        self.assertNotEqual(layer2_idx, -1)
        self.assertLess(layer0_idx, layer2_idx)
        self.assertIn("PYTHON CAPABILITY STANDARDS", composed_prompt)

    def test_truth_engine_plugin_claim_demotion(self):
        """4. Tests Truth Engine: Plugin self-declared VERIFIED_FACT is demoted to HYPOTHESIS if lacking level 4/5 evidence."""
        graph_store = EpistemicGraphStore()

        # Without level 4 evidence -> demoted to HYPOTHESIS
        c1 = graph_store.create_plugin_claim(
            plugin_id="aegis.capability.python",
            statement="Self declared fact without spec evidence",
            requested_state=EpistemicState.VERIFIED_FACT,
            evidence_level=EvidenceLevel.LEVEL_1_PARAMETRIC
        )
        self.assertEqual(c1.state, EpistemicState.HYPOTHESIS)
        self.assertIn("plugin:aegis.capability.python", c1.evidence_refs)

        # With level 4 specification evidence -> retained as VERIFIED_FACT
        c2 = graph_store.create_plugin_claim(
            plugin_id="aegis.capability.python",
            statement="Verified claim with specification evidence",
            requested_state=EpistemicState.VERIFIED_FACT,
            evidence_level=EvidenceLevel.LEVEL_4_SPECIFICATION
        )
        self.assertEqual(c2.state, EpistemicState.VERIFIED_FACT)

    def test_quality_engine_plugin_validator_registration(self):
        """5. Tests Quality Engine: Adding custom plugin validator and verifying AST syntax check."""
        quality_pipeline = QualityPipeline(self.config)
        py_plugin = PythonCapabilityPlugin()
        validators = py_plugin.get_capabilities()["validators"]
        quality_pipeline.register_validator(validators[0])

        # Test valid Python code block
        ctx_valid = QualityContext(
            system_prompt="sys",
            user_prompt="usr",
            model_response_text="Here is python code:\n```python\nx = 10 + 20\n```",
            config=self.config
        )
        report_valid = quality_pipeline.validate(ctx_valid)
        self.assertEqual(report_valid.result.status, QualityStatus.PASS)

        # Test code block with syntax error
        ctx_syntax_err = QualityContext(
            system_prompt="sys",
            user_prompt="usr",
            model_response_text="Invalid python:\n```python\ndef foo(:\n```",
            config=self.config
        )
        report_err = quality_pipeline.validate(ctx_syntax_err)
        self.assertEqual(report_err.result.status, QualityStatus.FAIL)

    def test_quality_engine_core_validator_protection(self):
        """6. Tests Quality Engine: Core system validators cannot be removed by plugins."""
        quality_pipeline = QualityPipeline(self.config)
        core_val = quality_pipeline._core_validators[0]
        with self.assertRaises(PermissionError):
            quality_pipeline.unregister_validator(core_val)

    def test_session_manager_plugin_memory_permission(self):
        """7. Tests Session Manager: Default DENY on memory write without explicit MEMORY_WRITE permission."""
        session_mgr = SessionManager(self.config)
        sess = session_mgr.create_session("user_100")

        # Without token -> PermissionError
        with self.assertRaises(PermissionError):
            session_mgr.set_plugin_memory(sess.session_id, "p1", "key", "val", token=None)

        # Token without MEMORY_WRITE permission -> PermissionError
        token_no_perm = CapabilityToken("p1", {PluginPermission.FILESYSTEM_READ})
        with self.assertRaises(PermissionError):
            session_mgr.set_plugin_memory(sess.session_id, "p1", "key", "val", token=token_no_perm)

        # Token with explicit MEMORY_WRITE permission -> Success
        token_with_perm = CapabilityToken("p1", {PluginPermission.MEMORY_WRITE})
        success = session_mgr.set_plugin_memory(sess.session_id, "p1", "key", "val", token=token_with_perm)
        self.assertTrue(success)

    def test_session_manager_lifecycle_hooks(self):
        """8. Tests Session Manager: Executing ON_SESSION_CREATE and ON_SESSION_DESTROY hooks."""
        session_mgr = SessionManager(self.config)
        events = []

        session_mgr.register_session_hook("ON_SESSION_CREATE", lambda s: events.append(f"CREATE:{s.session_id}"))
        session_mgr.register_session_hook("ON_SESSION_DESTROY", lambda s: events.append(f"DESTROY:{s.session_id}"))

        sess = session_mgr.create_session("user_200", session_id="SESS_TEST_HOOKS")
        self.assertIn("CREATE:SESS_TEST_HOOKS", events)

        session_mgr.terminate_session("SESS_TEST_HOOKS")
        self.assertIn("DESTROY:SESS_TEST_HOOKS", events)

    def test_model_gateway_custom_provider_extension(self):
        """9. Tests ModelGatewayFactory: Registering and retrieving custom plugin model provider."""
        ModelGatewayFactory.register_provider("custom_plugin_provider", lambda cfg: CustomTestModelProvider())
        provider = ModelGatewayFactory.get_provider("custom_plugin_provider", self.config)
        resp = provider.generate("sys", "Hello test")
        self.assertIn("[Custom Plugin Provider Output]", resp.text)
        self.assertEqual(resp.provider, "custom_plugin_provider")

    def test_orchestrator_pipeline_hooks_execution(self):
        """10. Tests RuntimeOrchestrator: Executing BEFORE_INTENT and AFTER_DELIVERY plugin hooks."""
        hook_events = []
        py_plugin = PythonCapabilityPlugin()
        py_plugin.get_hook_handlers = lambda: {
            PluginHook.BEFORE_INTENT: lambda c: hook_events.append("HOOK_BEFORE_INTENT"),
            PluginHook.AFTER_DELIVERY: lambda c: hook_events.append("HOOK_AFTER_DELIVERY"),
        }

        self.manager.register_builtin(py_plugin)
        self.manager.activate_all({"aegis.capability.python": py_plugin})

        orchestrator = RuntimeOrchestrator(self.config, plugin_manager=self.manager)
        final_ctx = orchestrator.run("Write Python code for security auditing")

        self.assertIn("HOOK_BEFORE_INTENT", hook_events)
        self.assertIn("HOOK_AFTER_DELIVERY", hook_events)
        self.assertEqual(final_ctx.quality_result.status, QualityStatus.PASS)

    def test_orchestrator_custom_plugin_pipeline_stage(self):
        """11. Tests RuntimeOrchestrator: Inserting custom plugin PipelineStage."""
        class CustomPluginStage(PipelineStage):
            def __init__(self):
                super().__init__("CustomPluginStage")

            def execute(self, context: OrchestratorContext, tracer: PipelineTracer) -> StageResult:
                meta = dict(context.metadata)
                meta["custom_plugin_stage_ran"] = True
                return StageResult(success=True, context=context.copy_with(metadata=meta))

        orchestrator = RuntimeOrchestrator(self.config)
        orchestrator.register_stage(CustomPluginStage(), position=1)
        final_ctx = orchestrator.run("Test custom plugin stage insertion")
        self.assertTrue(final_ctx.metadata.get("custom_plugin_stage_ran"))

    def test_security_plugin_secret_scanner_integration(self):
        """12. Tests Security Capability Plugin: Detecting secret key leaks in model output."""
        quality_pipeline = QualityPipeline(self.config)
        sec_plugin = SecurityCapabilityPlugin()
        sec_validator = sec_plugin.get_capabilities()["validators"][0]
        quality_pipeline.register_validator(sec_validator)

        # Context containing leaked private key
        leak_text = "Here is the key:\n-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA...\n-----END RSA PRIVATE KEY-----\n"
        ctx = QualityContext("sys", "usr", leak_text, self.config)
        report = quality_pipeline.validate(ctx)

        self.assertEqual(report.result.status, QualityStatus.FAIL)
        self.assertTrue(any(issue.rule == QualityRule.PROMPT_INJECTION_RESIDUE for issue in report.result.issues))

    def test_plugin_cli_create_command(self):
        """13. Tests CLI Aegis Plugin SDK: 'create' command generates plugin scaffolding."""
        from runtime.src.cli import handle_plugin_cli
        import argparse

        args = argparse.Namespace(plugin_command="create", name="demo_created_plugin")
        handle_plugin_cli(args, self.config)

        created_dir = os.path.join(self.config.base_dir, "plugins", "demo_created_plugin")
        self.assertTrue(os.path.exists(os.path.join(created_dir, "manifest.yaml")))
        self.assertTrue(os.path.exists(os.path.join(created_dir, "plugin.py")))

        # Clean up created dir
        shutil.rmtree(created_dir, ignore_errors=True)

    def test_plugin_cli_validate_command(self):
        """14. Tests CLI Aegis Plugin SDK: 'validate' command validates manifest."""
        from runtime.src.cli import handle_plugin_cli
        import argparse

        plugin_dir = os.path.join(self.plugins_dir, "python_capability_plugin")
        args = argparse.Namespace(plugin_command="validate", path=plugin_dir)
        # Should execute cleanly without sys.exit
        handle_plugin_cli(args, self.config)

    def test_plugin_cli_package_command(self):
        """15. Tests CLI Aegis Plugin SDK: 'package' command creates zip archive."""
        from runtime.src.cli import handle_plugin_cli
        import argparse

        plugin_dir = os.path.join(self.plugins_dir, "security_capability_plugin")
        args = argparse.Namespace(plugin_command="package", path=plugin_dir)
        handle_plugin_cli(args, self.config)

        zip_path = os.path.join(self.plugins_dir, "security_capability_plugin.aegis-plugin.zip")
        self.assertTrue(os.path.exists(zip_path))

        # Clean up created zip
        if os.path.exists(zip_path):
            os.remove(zip_path)

    def test_plugin_cli_list_command(self):
        """16. Tests CLI Aegis Plugin SDK: 'list' command lists discovered plugins."""
        from runtime.src.cli import handle_plugin_cli
        import argparse

        args = argparse.Namespace(plugin_command="list")
        handle_plugin_cli(args, self.config)

    def test_plugin_cli_info_command(self):
        """17. Tests CLI Aegis Plugin SDK: 'info' command prints plugin metadata."""
        from runtime.src.cli import handle_plugin_cli
        import argparse

        self.manager.discover_plugins()
        args = argparse.Namespace(plugin_command="info", name="aegis.capability.python")
        handle_plugin_cli(args, self.config)

    def test_plugin_cli_enable_disable_command(self):
        """18. Tests CLI Aegis Plugin SDK: 'enable' and 'disable' commands."""
        from runtime.src.cli import handle_plugin_cli
        import argparse

        self.manager.discover_plugins()

        dis_args = argparse.Namespace(plugin_command="disable", name="aegis.capability.python")
        handle_plugin_cli(dis_args, self.config)

        # Test enable/disable directly on manager instance
        self.assertTrue(self.manager.disable_plugin("aegis.capability.python"))
        meta = self.manager.registry.get_metadata("aegis.capability.python")
        if meta:
            self.assertFalse(meta.enabled)

        self.assertTrue(self.manager.enable_plugin("aegis.capability.python"))
        if meta:
            self.assertTrue(meta.enabled)



if __name__ == "__main__":
    unittest.main()
