"""
Aegis AI Operating System — Hot Reload Safety Tests
Tests to verify that plugin hot-reload properly rolls back on failure
and never leaves the plugin system in a corrupted state.
"""

import unittest
import threading
from runtime.src.plugin import (
    AegisPlugin, PluginManifest, PluginContext, PluginManager,
    PluginCapability, PluginPermission, PluginHook, PluginState,
    PluginMetadata, PluginError, PluginLifecycleError,
    PluginPromptContribution,
)


class StablePlugin(AegisPlugin):
    """A well-behaved plugin that always succeeds."""

    def __init__(self, version="1.0.0"):
        self._version = version
        self.initialized = False
        self.activated = False

    def get_manifest(self) -> PluginManifest:
        return PluginManifest(
            plugin_id="test.stable.plugin",
            name="Stable Plugin",
            version=self._version,
            capabilities=[PluginCapability.PIPELINE_STAGE],
            permissions=[PluginPermission.FILESYSTEM_READ],
            hooks=[PluginHook.BEFORE_INTENT],
        )

    def on_initialize(self, ctx: PluginContext) -> bool:
        self.initialized = True
        return True

    def on_activate(self, ctx: PluginContext) -> bool:
        self.activated = True
        return True

    def on_suspend(self, ctx: PluginContext) -> bool:
        return True

    def on_resume(self, ctx: PluginContext) -> bool:
        return True

    def get_hook_handlers(self):
        return {PluginHook.BEFORE_INTENT: lambda ctx: "stable_hook_result"}

    def get_prompt_contributions(self):
        return [PluginPromptContribution(
            plugin_id="test.stable.plugin",
            content="Stable plugin contribution",
            section="test",
            priority=100,
        )]


class FailingInitPlugin(AegisPlugin):
    """A plugin that fails during on_initialize."""

    def get_manifest(self) -> PluginManifest:
        return PluginManifest(
            plugin_id="test.stable.plugin",
            name="Failing Init Plugin",
            version="2.0.0",
        )

    def on_initialize(self, ctx: PluginContext) -> bool:
        return False  # Initialization fails

    def on_activate(self, ctx: PluginContext) -> bool:
        return True


class ExplodingActivatePlugin(AegisPlugin):
    """A plugin that throws an exception during on_activate."""

    def get_manifest(self) -> PluginManifest:
        return PluginManifest(
            plugin_id="test.stable.plugin",
            name="Exploding Activate Plugin",
            version="2.0.0",
        )

    def on_initialize(self, ctx: PluginContext) -> bool:
        return True

    def on_activate(self, ctx: PluginContext) -> bool:
        raise RuntimeError("BOOM! Activation catastrophic failure")


class CrashingInitPlugin(AegisPlugin):
    """A plugin that throws an exception during on_initialize."""

    def get_manifest(self) -> PluginManifest:
        return PluginManifest(
            plugin_id="test.stable.plugin",
            name="Crashing Init Plugin",
            version="2.0.0",
        )

    def on_initialize(self, ctx: PluginContext) -> bool:
        raise ValueError("Critical init failure: corrupt state!")

    def on_activate(self, ctx: PluginContext) -> bool:
        return True


class TestHotReloadRollback(unittest.TestCase):
    """Tests that hot-reload rolls back to old plugin on failure."""

    def _setup_active_plugin(self):
        """Creates a PluginManager with a fully active StablePlugin."""
        import tempfile
        import os
        tmpdir = tempfile.mkdtemp()
        manager = PluginManager(tmpdir)

        old_instance = StablePlugin(version="1.0.0")
        manifest = manager.register_builtin(old_instance)
        plugin_id = manifest.plugin_id

        manager.load_plugin(plugin_id, old_instance)
        manager.validate_plugin(plugin_id)
        manager.resolve_dependencies()
        manager.activate_plugin(plugin_id)

        meta = manager.registry.get_metadata(plugin_id)
        self.assertEqual(meta.state, PluginState.ACTIVE)

        return manager, plugin_id, old_instance

    def test_reload_init_failure_rolls_back(self):
        """When new plugin on_initialize fails, old plugin should be restored."""
        manager, plugin_id, old_instance = self._setup_active_plugin()

        failing_new = FailingInitPlugin()
        with self.assertRaises(PluginError) as ctx:
            manager.reload_plugin(plugin_id, failing_new)

        self.assertIn("muvaffaqiyatsiz", str(ctx.exception).lower())

        # Verify old plugin is still active
        meta = manager.registry.get_metadata(plugin_id)
        self.assertEqual(meta.state, PluginState.ACTIVE)

        # Verify old instance is still registered
        current_instance = manager.registry.get_instance(plugin_id)
        self.assertIs(current_instance, old_instance)

    def test_reload_activate_exception_rolls_back(self):
        """When new plugin on_activate throws exception, old plugin should be restored."""
        manager, plugin_id, old_instance = self._setup_active_plugin()

        exploding_new = ExplodingActivatePlugin()
        with self.assertRaises(PluginError) as ctx:
            manager.reload_plugin(plugin_id, exploding_new)

        # Verify rollback
        meta = manager.registry.get_metadata(plugin_id)
        self.assertEqual(meta.state, PluginState.ACTIVE)

        current_instance = manager.registry.get_instance(plugin_id)
        self.assertIs(current_instance, old_instance)

    def test_reload_init_crash_rolls_back(self):
        """When new plugin on_initialize crashes, old plugin should be restored."""
        manager, plugin_id, old_instance = self._setup_active_plugin()

        crashing_new = CrashingInitPlugin()
        with self.assertRaises(PluginError):
            manager.reload_plugin(plugin_id, crashing_new)

        # Verify rollback preserved old state
        meta = manager.registry.get_metadata(plugin_id)
        self.assertEqual(meta.state, PluginState.ACTIVE)
        current = manager.registry.get_instance(plugin_id)
        self.assertIs(current, old_instance)

    def test_reload_failure_event_published(self):
        """Failed reload should publish PLUGIN_RELOAD_FAILED event."""
        manager, plugin_id, old_instance = self._setup_active_plugin()

        events = []
        manager.event_bus.subscribe(
            lambda e: events.append(e),
        )

        with self.assertRaises(PluginError):
            manager.reload_plugin(plugin_id, FailingInitPlugin())

        reload_failed_events = [e for e in events if e.event_type == "PLUGIN_RELOAD_FAILED"]
        self.assertTrue(len(reload_failed_events) > 0, "PLUGIN_RELOAD_FAILED event should be published")
        self.assertIn(reload_failed_events[0].payload.get("rollback"), ("SUCCESS", "PRESERVED_UNCHANGED"))

    def test_reload_prompt_contributions_restored(self):
        """After failed reload, prompt contributions should be restored."""
        manager, plugin_id, old_instance = self._setup_active_plugin()

        # Record initial contribution count
        initial_contribs = [c for c in manager.get_prompt_contributions()
                           if c.plugin_id == plugin_id]

        with self.assertRaises(PluginError):
            manager.reload_plugin(plugin_id, ExplodingActivatePlugin())

        # Verify contributions are restored
        restored_contribs = [c for c in manager.get_prompt_contributions()
                            if c.plugin_id == plugin_id]
        self.assertEqual(len(initial_contribs), len(restored_contribs))

    def test_successful_reload_works_normally(self):
        """Normal hot-reload should still work when new plugin succeeds."""
        manager, plugin_id, old_instance = self._setup_active_plugin()

        new_instance = StablePlugin(version="2.0.0")
        result = manager.reload_plugin(plugin_id, new_instance)
        self.assertTrue(result)

        meta = manager.registry.get_metadata(plugin_id)
        self.assertEqual(meta.state, PluginState.ACTIVE)

        current = manager.registry.get_instance(plugin_id)
        self.assertIs(current, new_instance)
        self.assertTrue(new_instance.initialized)
        self.assertTrue(new_instance.activated)


if __name__ == "__main__":
    unittest.main()
