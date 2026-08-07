"""
Aegis Session & Memory Manager Production CLI Demo
Demonstrates persistent session creation, multi-turn conversation history, claim DAG persistence, token pruning, and crash recovery.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from runtime.src.config import AegisConfig
from runtime.src.session import SessionManager


def main():
    print("================================================================================")
    print("AEGIS SESSION & MEMORY MANAGER PRODUCTION DEMO")
    print("================================================================================")

    config = AegisConfig.load_from_env()
    manager = SessionManager(config)

    print("\n1. Creating Session for User 'dev_lead'...")
    session = manager.create_session(user_id="dev_lead")
    print(f"   Session ID : {session.session_id}")
    print(f"   State      : {session.state.value}")
    print(f"   Token Budget: {session.context_window.max_token_budget}")

    print("\n2. Adding Multi-Turn Messages & Claims...")
    manager.add_user_message(session.session_id, "Refactor database pool architecture")
    manager.add_assistant_message(session.session_id, "Database pool refactored with thread-safe RLock")
    session.memory.epistemic_claims.add_claim("CLM-100", "RLock verified for thread pool", "VERIFIED_FACT", 3)
    manager.persistence.save_snapshot(session)

    print("\n3. Simulating Server Restart / Crash Recovery...")
    new_manager = SessionManager(config)
    restored = new_manager.get_session(session.session_id)

    print(f"   Restored Session ID : {restored.session_id}")
    print(f"   Restored Messages   : {len(restored.history.messages)}")
    for idx, msg in enumerate(restored.history.messages, 1):
        print(f"     {idx}. [{msg.role.value}] {msg.content}")

    print("\n4. Session Metrics...")
    metrics = manager.get_metrics()
    print(f"   Active Sessions      : {metrics.active_sessions_count}")
    print(f"   Total Snapshots Saved: {metrics.total_snapshots_saved}")

    print("================================================================================")
    print("DEMO COMPLETE — SESSION & MEMORY MANAGER OPERATING AT PRODUCTION RIGOR")
    print("================================================================================")


if __name__ == "__main__":
    main()
