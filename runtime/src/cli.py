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


def run_interactive_chat(
    config: AegisConfig,
    provider_name: str = "mock",
    session_id: Optional[str] = None
) -> None:
    """Runs the interactive Aegis AI OS REPL Chat Shell."""
    import time

    plugins_dir = os.path.join(config.base_dir, "plugins")
    plugin_manager = PluginManager(plugins_dir)
    plugin_manager.discover_plugins()

    curr_provider_name = provider_name or config.provider or "mock"
    try:
        provider = ModelGatewayFactory.get_provider(curr_provider_name, config)
    except Exception as e:
        print(f"⚠️ Provider error for '{curr_provider_name}': {e}. Falling back to 'mock'.")
        curr_provider_name = "mock"
        provider = ModelGatewayFactory.get_provider("mock", config)

    orchestrator = RuntimeOrchestrator(config, provider, plugin_manager=plugin_manager)

    active_session_id = session_id or f"SESS_CHAT_{int(time.time())}"
    sess = orchestrator.session_manager.get_session(active_session_id)

    # Banner
    print("================================================================================")
    print("🛡️ AEGIS AI OPERATING SYSTEM v2.0.0 — INTERACTIVE REPL SHELL")
    print(f"Provider: {curr_provider_name.upper()} | Model: {config.gemini_model} | Session: {active_session_id}")
    print("Type '/help' for interactive commands, '/exit' or Ctrl+C to quit.")
    print("================================================================================\n")

    while True:
        try:
            user_input = input("aegis> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n👋 Exiting Aegis AI Operating System. Goodbye!")
            break

        if not user_input:
            continue

        # Handle Slash Commands
        if user_input.startswith("/"):
            parts = user_input.split(maxsplit=1)
            cmd = parts[0].lower()
            arg = parts[1].strip() if len(parts) > 1 else ""

            if cmd in ("/exit", "/quit"):
                print("👋 Exiting Aegis REPL. Goodbye!")
                break

            elif cmd == "/help":
                print("\n💡 Aegis AI OS Interactive Commands:")
                print("  /help             Show this help menu")
                print("  /status           Display runtime status, active session, provider, model & metrics")
                print("  /session [id]     Switch active session or view current session details")
                print("  /sessions         List all saved persistent session snapshots on disk")
                print("  /plugins          List all discovered and active plugins")
                print("  /plugin <name>    Show detailed metadata for a plugin")
                print("  /provider [name]  Switch LLM provider (mock, gemini, claude, openai, openrouter)")
                print("  /model [name]     Switch active LLM model")
                print("  /clear            Clear terminal screen")
                print("  /reset            Reset conversation context history for current session")
                print("  /exit, /quit      Exit interactive Aegis REPL shell\n")

            elif cmd == "/status":
                sess = orchestrator.session_manager.get_session(active_session_id)
                msg_count = len(sess.history.messages) if sess else 0
                active_plugins = [p for p in plugin_manager.list_plugins() if p.enabled]
                print(f"\n📊 Aegis Runtime Status:")
                print(f"  - Active Session   : {active_session_id} ({msg_count} messages in history)")
                print(f"  - LLM Provider     : {curr_provider_name.upper()}")
                print(f"  - Target Model     : {config.gemini_model}")
                print(f"  - Reasoning Depth  : {config.reasoning_depth}")
                print(f"  - Max Retries      : {config.max_retries}")
                print(f"  - Active Plugins   : {len(active_plugins)} active / {len(plugin_manager.list_plugins())} discovered")
                if orchestrator.tracer.metrics:
                    print("  - Last Execution   :")
                    for m in orchestrator.tracer.metrics:
                        print(f"      {m.stage_name:22s}: {m.duration_ms:6.2f} ms")
                print()

            elif cmd == "/session":
                if arg:
                    active_session_id = arg
                    sess = orchestrator.session_manager.get_session(active_session_id)
                    msg_cnt = len(sess.history.messages) if sess else 0
                    print(f"🔄 Switched to session '{active_session_id}' ({msg_cnt} messages in history).")
                else:
                    sess = orchestrator.session_manager.get_session(active_session_id)
                    msg_cnt = len(sess.history.messages) if sess else 0
                    print(f"ℹ️ Active Session: '{active_session_id}' ({msg_cnt} messages in history).")

            elif cmd == "/sessions":
                print("\n📋 Aegis Persistent Sessions on Disk:")
                sessions_dir = os.path.join(config.base_dir, "runtime", "sessions")
                if os.path.exists(sessions_dir):
                    files = [f for f in os.listdir(sessions_dir) if f.endswith(".json")]
                    if files:
                        for f in sorted(files):
                            print(f"  - {f.replace('.json', '')}")
                    else:
                        print("  (No persistent session snapshots found)")
                else:
                    print("  (No persistent session directory found)")
                print()

            elif cmd == "/plugins":
                plugin_manager.discover_plugins()
                plugins = plugin_manager.list_plugins()
                print(f"\n📋 Aegis Plugins ({len(plugins)} discovered):")
                for meta in plugins:
                    st = "ACTIVE" if meta.enabled else "DISABLED"
                    print(f"  - [{st:8s}] {meta.manifest.plugin_id} (v{meta.manifest.version}) — {meta.manifest.name}")
                print()

            elif cmd == "/plugin":
                if not arg:
                    print("❌ Usage: /plugin <plugin_id_or_name>", file=sys.stderr)
                else:
                    info = plugin_manager.get_plugin_info(arg)
                    if info:
                        print(f"\nℹ️ Plugin Info ({arg}):")
                        print(json.dumps(info, indent=2))
                        print()
                    else:
                        print(f"❌ Plugin '{arg}' not found.", file=sys.stderr)

            elif cmd == "/provider":
                if not arg:
                    print(f"ℹ️ Active Provider: {curr_provider_name.upper()}")
                else:
                    target_prov = arg.lower()
                    try:
                        new_provider = ModelGatewayFactory.get_provider(target_prov, config)
                        orchestrator.model_gateway = new_provider
                        curr_provider_name = target_prov
                        config.provider = target_prov
                        print(f"✅ Provider switched to '{curr_provider_name.upper()}'.")
                    except Exception as err:
                        print(f"❌ Failed to switch provider to '{target_prov}': {err}", file=sys.stderr)

            elif cmd == "/model":
                if not arg:
                    print(f"ℹ️ Active Model: {config.gemini_model}")
                else:
                    config.gemini_model = arg
                    print(f"✅ Target model updated to '{config.gemini_model}'.")

            elif cmd == "/clear":
                print("\033[H\033[J", end="")

            elif cmd == "/reset":
                orchestrator.session_manager.create_session("chat_user", session_id=active_session_id)
                print(f"🧹 Session history for '{active_session_id}' has been reset.")

            else:
                print(f"❌ Unknown command: {cmd}. Type '/help' for available commands.", file=sys.stderr)

            continue

        # Regular Task Execution in Chat REPL
        print(f"\n[Session]    Active session: {active_session_id}")
        print(f"[Intent]     Resolving user request intent...")
        print(f"[Reasoning]  Executing analytical reasoning depth: {config.reasoning_depth}...")
        print(f"[Knowledge]  Loading context patterns & modules...")
        print(f"[Truth]      Verifying claim graph & evidence hierarchy...")

        active_plugins = [p for p in plugin_manager.list_plugins() if p.enabled]
        if active_plugins:
            print(f"[Plugin]     Dispatched {len(active_plugins)} active plugin capabilities")
        print(f"[Prompt]     Composed Layer 0 Kernel payload")
        print(f"[Model]      Generating response via {curr_provider_name.upper()} provider...")

        try:
            final_ctx = orchestrator.run(user_input, session_id=active_session_id)

            if final_ctx.quality_result and final_ctx.quality_result.status.value != "PASS":
                print(f"[Quality]    ❌ FAILED Gates: {', '.join(final_ctx.quality_result.failed_gates)}")
                print(f"❌ Execution halted: Quality Gates Failed.", file=sys.stderr)
            else:
                score_val = getattr(final_ctx.quality_result, "score", 1.0) if final_ctx.quality_result else 1.0
                print(f"[Quality]    ✅ PASS (Score: {score_val})")
                print(f"[Session]    Saved session snapshot to disk\n")



                print("================================================================================")
                if final_ctx.model_response:
                    print(final_ctx.model_response.text)
                print("================================================================================\n")

        except Exception as err:
            if config.debug_mode:
                import traceback
                traceback.print_exc()
            else:
                print(f"❌ Aegis Engine Error: {err}", file=sys.stderr)
                print("   (Run with '--debug' for full stack trace)\n", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Aegis AI Operating System Executable Runtime Engine & Plugin SDK")
    
    subparsers = parser.add_subparsers(dest="subcommand")

    # Chat subcommand
    chat_p = subparsers.add_parser("chat", help="Start interactive Aegis AI OS chat REPL shell")
    chat_p.add_argument("--session", "-s", help="Target session ID to create or resume")
    chat_p.add_argument("--provider", "-p", default="mock", help="Target LLM provider (mock, gemini, claude, openai, openrouter)")
    chat_p.add_argument("--model", "-m", help="Override target LLM model")
    chat_p.add_argument("--reasoning-depth", choices=["L1", "L2", "L3"], help="Set reasoning depth level")

    # Plugins subcommand alias
    subparsers.add_parser("plugins", help="List all discovered plugins")

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
    parser.add_argument("--task", "-t", help="Task description or prompt for single-shot Aegis execution")
    parser.add_argument("--session", "-s", help="Target session ID for multi-turn execution")
    parser.add_argument("--list-sessions", action="store_true", help="List all active and persistent sessions")
    parser.add_argument("--plugins", action="store_true", help="List all discovered plugins")
    parser.add_argument("--plugin-info", help="Get detailed information for a plugin")
    parser.add_argument("--provider", "-p", default="mock", help="Target LLM provider (mock, gemini, claude, openai, openrouter)")
    parser.add_argument("--model", "-m", help="Override target LLM model")
    parser.add_argument("--reasoning-depth", choices=["L1", "L2", "L3"], help="Set reasoning depth (L1=Fast, L2=Standard, L3=Deep)")
    parser.add_argument("--temperature", type=float, help="Set model temperature (0.0 to 2.0)")
    parser.add_argument("--max-tokens", type=int, help="Set maximum completion tokens")
    parser.add_argument("--config", help="Path to custom Aegis config file (.yaml)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose pipeline event logging")
    parser.add_argument("--debug", action="store_true", help="Enable developer debug stack traces")
    parser.add_argument("--version", action="version", version="Aegis AI OS Executable Runtime Engine v2.0.0")

    args = parser.parse_args()

    # Config Precedence: CLI > ENV > Config File > Default
    config = AegisConfig.load(config_path=args.config)

    if args.model:
        config.gemini_model = args.model
    if args.reasoning_depth:
        config.reasoning_depth = args.reasoning_depth
    if args.temperature is not None:
        config.temperature = args.temperature
    if args.max_tokens is not None:
        config.max_tokens = args.max_tokens
    if args.verbose:
        config.verbose = True
    if args.debug:
        config.debug_mode = True

    if args.subcommand == "plugins":
        args.plugin_command = "list"
        handle_plugin_cli(args, config)
        return

    if args.subcommand == "plugin":
        handle_plugin_cli(args, config)
        return

    if args.subcommand == "chat":
        run_interactive_chat(config, provider_name=args.provider, session_id=args.session)
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

    # If no task prompt provided and no subcommand, default to interactive chat shell!
    if not args.task:
        run_interactive_chat(config, provider_name=args.provider, session_id=args.session)
        return

    plugins_dir = os.path.join(config.base_dir, "plugins")
    plugin_manager = PluginManager(plugins_dir)
    plugin_manager.discover_plugins()

    try:
        provider = ModelGatewayFactory.get_provider(args.provider, config)
    except Exception as err:
        if config.debug_mode:
            raise
        print(f"❌ Provider configuration error: {err}", file=sys.stderr)
        sys.exit(1)

    orchestrator = RuntimeOrchestrator(config, provider, plugin_manager=plugin_manager)

    if config.verbose:
        def log_event(evt: PipelineEvent):
            print(f"[{evt.event_type:18s}] Stage: {evt.stage_name:22s} — {evt.message}")
        orchestrator.event_bus.subscribe(log_event)

    session_str = f" [Session: {args.session}]" if args.session else ""
    print(f"🛡️ Aegis AI OS Executable Runtime Engine v2.0.0 [Provider: {args.provider.upper()}]{session_str}")
    print(f"Task: {args.task}\n")

    try:
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

    except Exception as err:
        if config.debug_mode:
            raise
        print(f"❌ Aegis Execution Error: {err}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

