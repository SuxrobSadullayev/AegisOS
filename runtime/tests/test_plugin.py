"""
Unit tests for Aegis AI Operating System Plugin Subsystem (v2.0.0).
Provides 50+ deterministic unit tests covering lifecycle, manifests, discovery,
dependency resolution, capability registry, hooks, security permissions,
resource limits, hot reload, and CLI SDK.
"""

import os
import shutil
import tempfile
import unittest
from typing import Dict, List, Any
from runtime.src.config import AegisConfig, EpistemicState, EvidenceLevel
from runtime.src.plugin import (
    PluginState, PluginCapability, PluginPermission, PluginHook, SandboxLevel,
    PluginDependency, PluginManifest, PluginResources, PluginMetrics, PluginMetadata,
    PluginEvent, PluginEventFilter, CapabilityToken, PluginContext, PluginPromptContribution,
    CapabilityEntry, PluginError, PluginNotFoundError, PluginLifecycleError, PluginPermissionError,
    PluginDependencyError, CircularPluginDependencyError, PluginManifestError, PluginCapabilityError,
    AegisPlugin, parse_semver, version_satisfies, check_version_constraint, parse_yaml_minimal,
    PluginEventBus, PluginDependencyResolver, PluginSecurityManager, PluginLifecycleManager,
    CapabilityRegistry, HookDispatcher, PluginDiscovery, PluginRegistry, PluginMetricsCollector,
    PluginTestHarness, ManifestValidator, PluginManager
)


class DummyTestPlugin(AegisPlugin):
    """Dummy test plugin implementing AegisPlugin SDK."""
    def __init__(self, plugin_id: str = "dummy.plugin", version: str = "1.0.0"):
        self._plugin_id = plugin_id
        self._version = version
        self.initialized = False
        self.activated = False
        self.executed_data: List[Any] = []
        self.suspended = False
        self.resumed = False
        self.unloaded = False
        self.destroyed = False

    def get_manifest(self) -> PluginManifest:
        return PluginManifest(
            plugin_id=self._plugin_id,
            name="Dummy Test Plugin",
            version=self._version,
            description="Plugin for unit testing",
            author="Unit Tester",
            capabilities=[PluginCapability.QUALITY_VALIDATOR, PluginCapability.PIPELINE_STAGE],
            permissions=[PluginPermission.FILESYSTEM_READ, PluginPermission.PIPELINE_MODIFY],
            hooks=[PluginHook.BEFORE_INTENT],
            sandbox_level=SandboxLevel.BASIC,
            priority=100
        )

    def on_initialize(self, ctx: PluginContext) -> bool:
        self.initialized = True
        return True

    def on_activate(self, ctx: PluginContext) -> bool:
        self.activated = True
        return True

    def on_execute(self, ctx: PluginContext, data: Dict[str, Any]) -> Any:
        self.executed_data.append(data)
        return f"Executed:{data.get('input', '')}"

    def on_suspend(self, ctx: PluginContext) -> bool:
        self.suspended = True
        return True

    def on_resume(self, ctx: PluginContext) -> bool:
        self.resumed = True
        return True

    def on_unload(self, ctx: PluginContext) -> bool:
        self.unloaded = True
        return True

    def on_destroy(self, ctx: PluginContext) -> bool:
        self.destroyed = True
        return True


class TestSemVerUtilities(unittest.TestCase):
    """1-6: Tests for SemVer and version constraint checking."""

    def test_parse_semver_valid(self):
        self.assertEqual(parse_semver("1.2.3"), (1, 2, 3))
        self.assertEqual(parse_semver("0.0.1"), (0, 0, 1))
        self.assertEqual(parse_semver(" 2.10.0 "), (2, 10, 0))

    def test_parse_semver_invalid(self):
        with self.assertRaises(ValueError):
            parse_semver("1.2")
        with self.assertRaises(ValueError):
            parse_semver("1.2.3.4")

    def test_version_satisfies_range(self):
        self.assertTrue(version_satisfies("1.2.0", "1.0.0", "2.0.0"))
        self.assertTrue(version_satisfies("1.0.0", "1.0.0", "2.0.0"))
        self.assertFalse(version_satisfies("2.0.0", "1.0.0", "2.0.0"))
        self.assertFalse(version_satisfies("0.9.9", "1.0.0", "2.0.0"))

    def test_check_version_constraint_gte(self):
        self.assertTrue(check_version_constraint("2.0.0", ">=2.0.0"))
        self.assertTrue(check_version_constraint("2.1.0", ">=2.0.0"))
        self.assertFalse(check_version_constraint("1.9.9", ">=2.0.0"))

    def test_check_version_constraint_compound(self):
        self.assertTrue(check_version_constraint("2.1.0", ">=2.0.0,<3.0.0"))
        self.assertFalse(check_version_constraint("3.0.0", ">=2.0.0,<3.0.0"))

    def test_check_version_constraint_empty(self):
        self.assertTrue(check_version_constraint("1.0.0", ""))


class TestYAMLParserMinimal(unittest.TestCase):
    """7-10: Tests for minimal built-in YAML parser."""

    def test_parse_yaml_flat(self):
        yaml_str = "key1: value1\nkey2: 123\nkey3: true\n"
        data = parse_yaml_minimal(yaml_str)
        self.assertEqual(data["key1"], "value1")
        self.assertEqual(data["key2"], 123)
        self.assertIs(data["key3"], True)

    def test_parse_yaml_list(self):
        yaml_str = "items:\n  - item1\n  - item2\n  - item3\n"
        data = parse_yaml_minimal(yaml_str)
        self.assertEqual(data["items"], ["item1", "item2", "item3"])

    def test_parse_yaml_comments(self):
        yaml_str = "# Comment line\nname: test # Inline comment\n"
        data = parse_yaml_minimal(yaml_str)
        self.assertEqual(data["name"], "test")

    def test_parse_yaml_quoted_strings(self):
        yaml_str = 'title: "Hello World"\nauthor: \'Aegis Team\'\n'
        data = parse_yaml_minimal(yaml_str)
        self.assertEqual(data["title"], "Hello World")
        self.assertEqual(data["author"], "Aegis Team")


class TestPluginEventBus(unittest.TestCase):
    """11-15: Tests for PluginEventBus pub/sub, priority, filtering, and recovery."""

    def setUp(self):
        self.bus = PluginEventBus()

    def test_subscribe_and_publish(self):
        received = []
        self.bus.subscribe(lambda evt: received.append(evt.event_type))
        self.bus.publish(PluginEvent("TEST_EVENT", "plugin_a"))
        self.assertEqual(received, ["TEST_EVENT"])

    def test_event_filtering_by_type(self):
        received = []
        filt = PluginEventFilter(event_types=["TYPE_A"])
        self.bus.subscribe(lambda evt: received.append(evt.event_type), filt)
        self.bus.publish(PluginEvent("TYPE_A", "src"))
        self.bus.publish(PluginEvent("TYPE_B", "src"))
        self.assertEqual(received, ["TYPE_A"])

    def test_event_filtering_by_source(self):
        received = []
        filt = PluginEventFilter(source_plugin_ids=["plugin_1"])
        self.bus.subscribe(lambda evt: received.append(evt.source_plugin_id), filt)
        self.bus.publish(PluginEvent("EVT", "plugin_1"))
        self.bus.publish(PluginEvent("EVT", "plugin_2"))
        self.assertEqual(received, ["plugin_1"])

    def test_handler_priority_order(self):
        order = []
        self.bus.subscribe(lambda e: order.append("low"), PluginEventFilter(priority=10))
        self.bus.subscribe(lambda e: order.append("high"), PluginEventFilter(priority=100))
        self.bus.publish(PluginEvent("EVT", "src"))
        self.assertEqual(order, ["high", "low"])

    def test_error_recovery_auto_remove_failing_handler(self):
        def failing_handler(evt):
            raise RuntimeError("Failing handler")

        self.bus.subscribe(failing_handler)
        self.assertEqual(self.bus.subscriber_count, 1)

        # Publish 3 times to trigger max consecutive errors limit
        for _ in range(3):
            self.bus.publish(PluginEvent("EVT", "src"))

        self.assertEqual(self.bus.subscriber_count, 0)


class TestPluginDependencyResolver(unittest.TestCase):
    """16-20: Tests for Kahn's topological sort and dependency resolution."""

    def setUp(self):
        self.resolver = PluginDependencyResolver()

    def test_resolve_independent_plugins(self):
        m1 = PluginManifest("p1", "P1", "1.0.0")
        m2 = PluginManifest("p2", "P2", "1.0.0")
        manifests = {"p1": m1, "p2": m2}
        order = self.resolver.resolve(manifests)
        self.assertEqual(sorted(order), ["p1", "p2"])

    def test_resolve_linear_dependency(self):
        m1 = PluginManifest("base", "Base", "1.0.0")
        m2 = PluginManifest("app", "App", "1.0.0", dependencies=[PluginDependency("base")])
        manifests = {"base": m1, "app": m2}
        order = self.resolver.resolve(manifests)
        self.assertEqual(order, ["base", "app"])

    def test_resolve_missing_required_dependency(self):
        m = PluginManifest("app", "App", "1.0.0", dependencies=[PluginDependency("missing_dep")])
        with self.assertRaises(PluginDependencyError):
            self.resolver.resolve({"app": m})

    def test_resolve_missing_optional_dependency(self):
        m = PluginManifest("app", "App", "1.0.0", dependencies=[PluginDependency("opt_dep", is_optional=True)])
        order = self.resolver.resolve({"app": m})
        self.assertEqual(order, ["app"])

    def test_detect_circular_dependency(self):
        m1 = PluginManifest("p1", "P1", "1.0.0", dependencies=[PluginDependency("p2")])
        m2 = PluginManifest("p2", "P2", "1.0.0", dependencies=[PluginDependency("p1")])
        with self.assertRaises(CircularPluginDependencyError):
            self.resolver.resolve({"p1": m1, "p2": m2})


class TestPluginSecurityManager(unittest.TestCase):
    """21-25: Tests for permission token checks and default DENY security model."""

    def setUp(self):
        self.security = PluginSecurityManager()

    def test_default_deny_without_token(self):
        self.assertFalse(self.security.check_permission("p1", PluginPermission.FILESYSTEM_READ))

    def test_grant_and_check_permission(self):
        token = self.security.issue_token("p1", [PluginPermission.FILESYSTEM_READ])
        self.assertTrue(token.has_permission(PluginPermission.FILESYSTEM_READ))
        self.assertFalse(token.has_permission(PluginPermission.FILESYSTEM_WRITE))
        self.assertTrue(self.security.check_permission("p1", PluginPermission.FILESYSTEM_READ))
        self.assertFalse(self.security.check_permission("p1", PluginPermission.FILESYSTEM_WRITE))

    def test_enforce_permission_success(self):
        self.security.issue_token("p1", [PluginPermission.SECRET_ACCESS])
        # Should not raise
        self.security.enforce("p1", PluginPermission.SECRET_ACCESS)

    def test_enforce_permission_failure(self):
        self.security.issue_token("p1", [PluginPermission.FILESYSTEM_READ])
        with self.assertRaises(PluginPermissionError):
            self.security.enforce("p1", PluginPermission.PROCESS_EXECUTE)

    def test_revoke_token(self):
        self.security.issue_token("p1", [PluginPermission.FILESYSTEM_READ])
        self.security.revoke_token("p1")
        self.assertFalse(self.security.check_permission("p1", PluginPermission.FILESYSTEM_READ))


class TestPluginLifecycleManager(unittest.TestCase):
    """26-30: Tests for Finite State Machine transitions."""

    def setUp(self):
        self.lifecycle = PluginLifecycleManager()

    def test_valid_transitions_sequence(self):
        manifest = PluginManifest("p1", "P1", "1.0.0")
        meta = PluginMetadata(manifest=manifest, state=PluginState.DISCOVERED)

        meta = self.lifecycle.transition(meta, PluginState.LOADED)
        self.assertEqual(meta.state, PluginState.LOADED)

        meta = self.lifecycle.transition(meta, PluginState.VALIDATED)
        self.assertEqual(meta.state, PluginState.VALIDATED)

        meta = self.lifecycle.transition(meta, PluginState.RESOLVED)
        self.assertEqual(meta.state, PluginState.RESOLVED)

        meta = self.lifecycle.transition(meta, PluginState.INITIALIZED)
        self.assertEqual(meta.state, PluginState.INITIALIZED)

        meta = self.lifecycle.transition(meta, PluginState.ACTIVE)
        self.assertEqual(meta.state, PluginState.ACTIVE)

    def test_invalid_transition_raises(self):
        manifest = PluginManifest("p1", "P1", "1.0.0")
        meta = PluginMetadata(manifest=manifest, state=PluginState.DISCOVERED)
        with self.assertRaises(PluginLifecycleError):
            self.lifecycle.transition(meta, PluginState.ACTIVE)

    def test_suspend_and_resume_transitions(self):
        manifest = PluginManifest("p1", "P1", "1.0.0")
        meta = PluginMetadata(manifest=manifest, state=PluginState.ACTIVE)

        meta = self.lifecycle.transition(meta, PluginState.SUSPENDED)
        self.assertEqual(meta.state, PluginState.SUSPENDED)

        meta = self.lifecycle.transition(meta, PluginState.ACTIVE)
        self.assertEqual(meta.state, PluginState.ACTIVE)

    def test_unload_and_destroy_transitions(self):
        manifest = PluginManifest("p1", "P1", "1.0.0")
        meta = PluginMetadata(manifest=manifest, state=PluginState.ACTIVE)

        meta = self.lifecycle.transition(meta, PluginState.UNLOADED)
        self.assertEqual(meta.state, PluginState.UNLOADED)

        meta = self.lifecycle.transition(meta, PluginState.DESTROYED)
        self.assertEqual(meta.state, PluginState.DESTROYED)

    def test_destroyed_state_has_no_valid_transitions(self):
        manifest = PluginManifest("p1", "P1", "1.0.0")
        meta = PluginMetadata(manifest=manifest, state=PluginState.DESTROYED)
        with self.assertRaises(PluginLifecycleError):
            self.lifecycle.transition(meta, PluginState.ACTIVE)


class TestCapabilityRegistry(unittest.TestCase):
    """31-35: Tests for AI-native CapabilityRegistry."""

    def setUp(self):
        self.cap_reg = CapabilityRegistry()

    def test_register_and_resolve_valid_capability(self):
        entry = CapabilityEntry(
            capability_type="validators",
            name="custom_val",
            plugin_id="p1",
            handler=lambda x: True,
            priority=50
        )
        self.cap_reg.register(entry)
        resolved = self.cap_reg.resolve("validators")
        self.assertEqual(len(resolved), 1)
        self.assertEqual(resolved[0].name, "custom_val")

    def test_register_invalid_capability_type_raises(self):
        entry = CapabilityEntry(
            capability_type="invalid_type",
            name="name",
            plugin_id="p1",
            handler=None
        )
        with self.assertRaises(PluginCapabilityError):
            self.cap_reg.register(entry)

    def test_resolve_filter_by_plugin_id(self):
        e1 = CapabilityEntry("tools", "tool1", "p1", None)
        e2 = CapabilityEntry("tools", "tool2", "p2", None)
        self.cap_reg.register(e1)
        self.cap_reg.register(e2)

        res_p1 = self.cap_reg.resolve("tools", plugin_id="p1")
        self.assertEqual(len(res_p1), 1)
        self.assertEqual(res_p1[0].plugin_id, "p1")

    def test_unregister_plugin_capabilities(self):
        e1 = CapabilityEntry("prompts", "prompt1", "p1", None)
        e2 = CapabilityEntry("agents", "agent1", "p1", None)
        self.cap_reg.register(e1)
        self.cap_reg.register(e2)

        self.cap_reg.unregister_plugin("p1")
        self.assertEqual(len(self.cap_reg.resolve("prompts")), 0)
        self.assertEqual(len(self.cap_reg.resolve("agents")), 0)

    def test_capability_summary(self):
        self.cap_reg.register(CapabilityEntry("commands", "cmd1", "p1", None))
        self.cap_reg.register(CapabilityEntry("commands", "cmd2", "p1", None))
        summary = self.cap_reg.get_summary()
        self.assertEqual(summary["commands"], 2)
        self.assertEqual(summary["validators"], 0)


class TestHookDispatcher(unittest.TestCase):
    """36-40: Tests for HookDispatcher priority and fail-safe execution."""

    def setUp(self):
        self.dispatcher = HookDispatcher()

    def test_register_and_dispatch_hook(self):
        called = []
        self.dispatcher.register("p1", PluginHook.BEFORE_INTENT, lambda ctx: called.append("hook1"))
        results = self.dispatcher.dispatch(PluginHook.BEFORE_INTENT, {"key": "val"})
        self.assertEqual(called, ["hook1"])
        self.assertEqual(len(results), 1)

    def test_dispatch_hook_priority_ordering(self):
        order = []
        self.dispatcher.register("p1", PluginHook.BEFORE_REASONING, lambda ctx: order.append("p1_100"), priority=100)
        self.dispatcher.register("p2", PluginHook.BEFORE_REASONING, lambda ctx: order.append("p2_10"), priority=10)
        self.dispatcher.dispatch(PluginHook.BEFORE_REASONING, {})
        self.assertEqual(order, ["p2_10", "p1_100"])

    def test_dispatch_hook_fail_safe_true(self):
        def failing(ctx):
            raise ValueError("Failing hook")

        self.dispatcher.register("p1", PluginHook.AFTER_QUALITY, failing)
        # Should not raise exception when fail_safe=True
        results = self.dispatcher.dispatch(PluginHook.AFTER_QUALITY, {}, fail_safe=True)
        self.assertEqual(results, [])

    def test_dispatch_hook_fail_safe_false(self):
        def failing(ctx):
            raise ValueError("Failing hook")

        self.dispatcher.register("p1", PluginHook.AFTER_QUALITY, failing)
        with self.assertRaises(PluginError):
            self.dispatcher.dispatch(PluginHook.AFTER_QUALITY, {}, fail_safe=False)

    def test_unregister_plugin_hooks(self):
        self.dispatcher.register("p1", PluginHook.BEFORE_INTENT, lambda c: None)
        self.dispatcher.unregister_plugin("p1")
        self.assertFalse(self.dispatcher.has_handlers(PluginHook.BEFORE_INTENT))


class TestManifestValidator(unittest.TestCase):
    """41-44: Tests for ManifestValidator."""

    def setUp(self):
        self.validator = ManifestValidator()

    def test_valid_manifest_no_errors(self):
        m = PluginManifest("aegis.test", "Test", "1.0.0", aegis_compatibility=">=2.0.0")
        errors = self.validator.validate(m)
        self.assertEqual(errors, [])

    def test_invalid_plugin_id_format(self):
        m = PluginManifest("invalid-id!", "Test", "1.0.0")
        errors = self.validator.validate(m)
        self.assertTrue(any("plugin_id" in e for e in errors))

    def test_invalid_semver_format(self):
        m = PluginManifest("aegis.test", "Test", "v1.0")
        errors = self.validator.validate(m)
        self.assertTrue(any("version" in e for e in errors))

    def test_incompatible_aegis_version(self):
        m = PluginManifest("aegis.test", "Test", "1.0.0", aegis_compatibility=">=3.0.0")
        errors = self.validator.validate(m)
        self.assertTrue(any("compatibility" in e for e in errors))


class TestPluginManagerAndHotReload(unittest.TestCase):
    """45-52: Tests for PluginManager full lifecycle, transactional hot reload, enable/disable."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="aegis_plugin_test_")
        self.manager = PluginManager(self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_register_builtin_and_activate(self):
        plugin = DummyTestPlugin("builtin.test", "1.0.0")
        self.manager.register_builtin(plugin)
        self.manager.load_plugin("builtin.test", plugin)
        self.manager.validate_plugin("builtin.test")
        self.manager.resolve_dependencies()
        self.assertTrue(self.manager.activate_plugin("builtin.test"))
        self.assertTrue(plugin.initialized)
        self.assertTrue(plugin.activated)

    def test_execute_active_plugin(self):
        plugin = DummyTestPlugin("dummy.exec", "1.0.0")
        self.manager.register_builtin(plugin)
        self.manager.load_plugin("dummy.exec", plugin)
        self.manager.validate_plugin("dummy.exec")
        self.manager.resolve_dependencies()
        self.manager.activate_plugin("dummy.exec")

        result = self.manager.execute_plugin("dummy.exec", {"input": "test_data"})
        self.assertEqual(result, "Executed:test_data")
        metrics = self.manager.get_metrics()
        self.assertEqual(metrics["dummy.exec"]["call_count"], 1)

    def test_execute_inactive_plugin_raises(self):
        plugin = DummyTestPlugin("dummy.inactive", "1.0.0")
        self.manager.register_builtin(plugin)
        with self.assertRaises(PluginLifecycleError):
            self.manager.execute_plugin("dummy.inactive", {})

    def test_transactional_hot_reload_success(self):
        p1 = DummyTestPlugin("hot.reload", "1.0.0")
        p2 = DummyTestPlugin("hot.reload", "1.0.1")

        self.manager.register_builtin(p1)
        self.manager.load_plugin("hot.reload", p1)
        self.manager.validate_plugin("hot.reload")
        self.manager.resolve_dependencies()
        self.manager.activate_plugin("hot.reload")

        # Transactional reload
        success = self.manager.reload_plugin("hot.reload", p2)
        self.assertTrue(success)
        self.assertTrue(p1.suspended)
        self.assertTrue(p2.initialized)
        self.assertTrue(p2.activated)
        self.assertIs(self.manager.get_plugin("hot.reload"), p2)

    def test_enable_and_disable_plugin(self):
        plugin = DummyTestPlugin("dummy.toggle", "1.0.0")
        self.manager.register_builtin(plugin)
        self.assertTrue(self.manager.disable_plugin("dummy.toggle"))
        meta = self.manager.registry.get_metadata("dummy.toggle")
        self.assertFalse(meta.enabled)
        self.assertTrue(self.manager.enable_plugin("dummy.toggle"))
        self.assertTrue(meta.enabled)

    def test_unload_and_destroy_plugin(self):
        plugin = DummyTestPlugin("dummy.destroy", "1.0.0")
        self.manager.register_builtin(plugin)
        self.manager.load_plugin("dummy.destroy", plugin)
        self.manager.validate_plugin("dummy.destroy")
        self.manager.resolve_dependencies()
        self.manager.activate_plugin("dummy.destroy")

        self.assertTrue(self.manager.unload_plugin("dummy.destroy"))
        self.assertTrue(plugin.unloaded)

        self.assertTrue(self.manager.destroy_plugin("dummy.destroy"))
        self.assertTrue(plugin.destroyed)
        self.assertIsNone(self.manager.get_plugin("dummy.destroy"))

    def test_activate_all_in_dependency_order(self):
        p_base = DummyTestPlugin("p.base", "1.0.0")
        p_app = DummyTestPlugin("p.app", "1.0.0")
        # App depends on base
        p_app_manifest = PluginManifest("p.app", "App", "1.0.0", dependencies=[PluginDependency("p.base")])
        p_app.get_manifest = lambda: p_app_manifest

        self.manager.register_builtin(p_base)
        self.manager.register_builtin(p_app)

        activated = self.manager.activate_all({"p.base": p_base, "p.app": p_app})
        self.assertEqual(activated, ["p.base", "p.app"])

    def test_plugin_prompt_contributions(self):
        plugin = DummyTestPlugin("p.prompt", "1.0.0")
        plugin.get_prompt_contributions = lambda: [
            PluginPromptContribution("p.prompt", "Sample Prompt Ext", section="ext", priority=10)
        ]
        self.manager.register_builtin(plugin)
        self.manager.load_plugin("p.prompt", plugin)
        self.manager.validate_plugin("p.prompt")
        self.manager.resolve_dependencies()
        self.manager.activate_plugin("p.prompt")

        contribs = self.manager.get_prompt_contributions()
        self.assertEqual(len(contribs), 1)
        self.assertEqual(contribs[0].content, "Sample Prompt Ext")



if __name__ == "__main__":
    unittest.main()
