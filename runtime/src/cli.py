"""
Modul 9: CLI & Runtime Executable Entrypoint
Main command-line entrypoint for the Aegis Executable Runtime Engine, powered by RuntimeOrchestrator,
with full Aegis Plugin SDK CLI support.
"""

import os
import sys
import json
import zipfile
import argparse
from typing import Optional
from runtime.src.config import AegisConfig
from runtime.src.gateway import ModelGatewayFactory
from runtime.src.orchestrator import RuntimeOrchestrator, PipelineEvent
from runtime.src.plugin import (
    PluginManager, PluginManifest, PluginTestHarness, ManifestValidator, PluginCapability
)


def handle_plugin_cli(args: argparse.Namespace, config: AegisConfig) -> None:
    """Handles Aegis Plugin SDK CLI subcommands."""
    plugins_dir = os.path.join(config.base_dir, "plugins")
    manager = PluginManager(plugins_dir)

    cmd = getattr(args, "plugin_command", None)

    if cmd == "create":
        name = args.name
        safe_id = f"aegis.plugin.{name.lower().replace('-', '_')}"
        target_dir = os.path.join(plugins_dir, name)
        os.makedirs(target_dir, exist_ok=True)

        manifest_content = (
            f"plugin_id: \"{safe_id}\"\n"
            f"name: \"{name.title()} Plugin\"\n"
            f"version: \"1.0.0\"\n"
            f"description: \"Custom Aegis plugin for {name}\"\n"
            f"author: \"Aegis Developer\"\n"
            f"capabilities:\n"
            f"  - PIPELINE_STAGE\n"
            f"  - QUALITY_VALIDATOR\n"
            f"permissions:\n"
            f"  - FILESYSTEM_READ\n"
            f"hooks:\n"
            f"  - BEFORE_INTENT\n"
            f"sandbox_level: \"BASIC\"\n"
            f"priority: 100\n"
        )
        with open(os.path.join(target_dir, "manifest.yaml"), "w", encoding="utf-8") as f:
            f.write(manifest_content)

        plugin_code = (
            "from runtime.src.plugin import AegisPlugin, PluginManifest, PluginContext\n\n"
            "class CustomPlugin(AegisPlugin):\n"
            "    def get_manifest(self) -> PluginManifest:\n"
            "        from runtime.src.plugin import PluginDiscovery\n"
            "        d = PluginDiscovery()\n"
            "        return d._parse_yaml_manifest('manifest.yaml')\n\n"
            "    def on_initialize(self, ctx: PluginContext) -> bool:\n"
            "        return True\n"
        )
        with open(os.path.join(target_dir, "plugin.py"), "w", encoding="utf-8") as f:
            f.write(plugin_code)

        print(f"✅ Plugin '{name}' successfully created at: {target_dir}")

    elif cmd == "validate":
        path = os.path.abspath(args.path)
        discovery = manager.discovery
        manifest = discovery._try_load_manifest(path) if os.path.isdir(path) else None
        if not manifest:
            print(f"❌ Validatsiya xatolik: '{path}' papkasida manifest.yaml/manifest.json topilmadi", file=sys.stderr)
            sys.exit(1)

        errors = ManifestValidator().validate(manifest)
        if errors:
            print(f"❌ Manifest xatolari ({manifest.plugin_id}):", file=sys.stderr)
            for err in errors:
                print(f"  - {err}", file=sys.stderr)
            sys.exit(1)
        else:
            print(f"✅ Manifest '{manifest.plugin_id}' v{manifest.version} muvaffaqiyatli validatsiyadan o'tdi.")

    elif cmd == "test":
        path = os.path.abspath(args.path)
        discovery = manager.discovery
        manifest = discovery._try_load_manifest(path)
        if not manifest:
            print(f"❌ Test xatolik: '{path}' papkasida manifest topilmadi", file=sys.stderr)
            sys.exit(1)

        harness = PluginTestHarness()
        ctx = harness.create_test_context(manifest.plugin_id)
        print(f"🧪 Plugin '{manifest.plugin_id}' test qilindi. Test context: {ctx.plugin_id}")
        print("✅ Plugin test muvaffaqiyatli yakunlandi.")

    elif cmd == "package":
        path = os.path.abspath(args.path)
        if not os.path.isdir(path):
            print(f"❌ Pakatlash xatolik: '{path}' papka emas", file=sys.stderr)
            sys.exit(1)

        zip_name = f"{os.path.basename(path)}.aegis-plugin.zip"
        zip_path = os.path.join(os.path.dirname(path), zip_name)

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(path):
                for file in files:
                    full_file = os.path.join(root, file)
                    rel_file = os.path.relpath(full_file, path)
                    zipf.write(full_file, rel_file)

        print(f"📦 Plugin muvaffaqiyatli paketlandi: {zip_path}")

    elif cmd == "list":
        manager.discover_plugins()
        plugins = manager.list_plugins()
        print(f"📋 Aegis Plugin'lar Ro'yxati ({len(plugins)} ta topildi):")
        for meta in plugins:
            status_str = "ACTIVE" if meta.enabled else "DISABLED"
            print(f"  - {meta.manifest.plugin_id} (v{meta.manifest.version}) [{status_str}] — {meta.manifest.name}")

    elif cmd == "info":
        name = args.name
        manager.discover_plugins()
        info = manager.get_plugin_info(name)
        if not info:
            print(f"❌ Plugin '{name}' topilmadi.", file=sys.stderr)
            sys.exit(1)
        print(f"ℹ️ Plugin Ma'lumotlari ({name}):")
        print(json.dumps(info, indent=2))

    elif cmd == "enable":
        name = args.name
        manager.discover_plugins()
        if manager.enable_plugin(name):
            print(f"✅ Plugin '{name}' yoqildi (enabled).")
        else:
            print(f"❌ Plugin '{name}' topilmadi.", file=sys.stderr)

    elif cmd == "disable":
        name = args.name
        manager.discover_plugins()
        if manager.disable_plugin(name):
            print(f"⏸️ Plugin '{name}' o'chirildi (disabled).")
        else:
            print(f"❌ Plugin '{name}' topilmadi.", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Aegis AI Operating System Executable Runtime Engine & Plugin SDK")
    
    subparsers = parser.add_subparsers(dest="subcommand")

    # Plugin subcommand
    plugin_parser = subparsers.add_parser("plugin", help="Aegis Plugin SDK buyruqlari")
    plugin_subparsers = plugin_parser.add_subparsers(dest="plugin_command")

    create_p = plugin_subparsers.add_parser("create", help="Yangi plugin yaratish")
    create_p.add_argument("name", help="Plugin nomi")

    val_p = plugin_subparsers.add_parser("validate", help="Plugin manifestini validatsiya qilish")
    val_p.add_argument("path", help="Plugin papkasi yo'li")

    test_p = plugin_subparsers.add_parser("test", help="Pluginni test qilish")
    test_p.add_argument("path", help="Plugin papkasi yo'li")

    pkg_p = plugin_subparsers.add_parser("package", help="Pluginni zip arxivga paketlash")
    pkg_p.add_argument("path", help="Plugin papkasi yo'li")

    plugin_subparsers.add_parser("list", help="Barcha pluginlarni ro'yxatga olish")

    info_p = plugin_subparsers.add_parser("info", help="Plugin haqida ma'lumot olish")
    info_p.add_argument("name", help="Plugin ID yoki nomi")

    enable_p = plugin_subparsers.add_parser("enable", help="Pluginni yoqish")
    enable_p.add_argument("name", help="Plugin ID")

    disable_p = plugin_subparsers.add_parser("disable", help="Pluginni o'chirish")
    disable_p.add_argument("name", help="Plugin ID")

    # Top-level arguments
    parser.add_argument("--task", "-t", help="Task description or prompt for Aegis")
    parser.add_argument("--session", "-s", help="Target session ID for multi-turn execution")
    parser.add_argument("--list-sessions", action="store_true", help="List all active and persistent sessions")
    parser.add_argument("--plugins", action="store_true", help="List all discovered plugins")
    parser.add_argument("--plugin-info", help="Get detailed information for a plugin")
    parser.add_argument("--provider", "-p", default="mock", help="Target LLM provider (mock, gemini, claude, openai, openrouter)")
    parser.add_argument("--model", "-m", help="Override target LLM model")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose pipeline event logging")
    parser.add_argument("--version", action="version", version="Aegis AI OS Executable Runtime Engine v2.0.0")

    args = parser.parse_args()

    config = AegisConfig.load_from_env()

    if args.subcommand == "plugin":
        handle_plugin_cli(args, config)
        return

    # Handle shorthand top-level flags
    if args.plugins:
        args.plugin_command = "list"
        handle_plugin_cli(args, config)
        return

    if args.plugin_info:
        args.plugin_command = "info"
        args.name = args.plugin_info
        handle_plugin_cli(args, config)
        return

    plugins_dir = os.path.join(config.base_dir, "plugins")
    plugin_manager = PluginManager(plugins_dir)
    plugin_manager.discover_plugins()

    provider = ModelGatewayFactory.get_provider(args.provider, config)
    orchestrator = RuntimeOrchestrator(config, provider, plugin_manager=plugin_manager)

    if args.list_sessions:
        print("📋 Aegis Session Persistence List:")
        sessions_dir = os.path.join(config.base_dir, "runtime", "sessions")
        if os.path.exists(sessions_dir):
            files = [f for f in os.listdir(sessions_dir) if f.endswith(".json")]
            if files:
                for f in sorted(files):
                    print(f"  - Session Snapshot: {f.replace('.json', '')}")
            else:
                print("  (No persistent session snapshots found)")
        else:
            print("  (No persistent session directory found)")
        return

    if not args.task:
        parser.print_help()
        sys.exit(0)

    if args.model:
        config.gemini_model = args.model

    if args.verbose:
        def log_event(evt: PipelineEvent):
            print(f"[{evt.event_type:18s}] Stage: {evt.stage_name:22s} — {evt.message}")
        orchestrator.event_bus.subscribe(log_event)

    session_str = f" [Session: {args.session}]" if args.session else ""
    print(f"🛡️ Aegis AI OS Executable Runtime Engine v2.0.0 [Provider: {args.provider.upper()}]{session_str}")
    print(f"Task: {args.task}\n")

    final_ctx = orchestrator.run(args.task, session_id=args.session)

    if final_ctx.quality_result and final_ctx.quality_result.status.value != "PASS":
        print(f"❌ Execution halted: Failed Quality Gates: {', '.join(final_ctx.quality_result.failed_gates)}", file=sys.stderr)
        sys.exit(1)

    print("=== TIMING METRICS (MS) ===")
    for metric in orchestrator.tracer.metrics:
        print(f"  - {metric.stage_name:25s}: {metric.duration_ms:6.2f} ms")

    print("\n================================================================================")
    if final_ctx.model_response:
        print(final_ctx.model_response.text)
    print("================================================================================")



if __name__ == "__main__":
    main()

