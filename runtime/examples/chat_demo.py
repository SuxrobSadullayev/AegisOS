"""
Aegis AI Operating System — Interactive Chat Engine Demonstration
Demonstrates programmatic usage of the Aegis REPL interactive chat shell.
"""

from runtime.src.config import AegisConfig
from runtime.src.cli import run_interactive_chat


def main():
    print("🛡️ Starting Aegis AI OS Interactive Chat Engine Demo...")
    config = AegisConfig.load()
    config.verbose = True
    config.reasoning_depth = "L2"

    # Start interactive chat shell in mock provider mode
    print("Starting interactive shell with session 'SESS_DEMO_CHAT'...")
    run_interactive_chat(config, provider_name="mock", session_id="SESS_DEMO_CHAT")


if __name__ == "__main__":
    main()
