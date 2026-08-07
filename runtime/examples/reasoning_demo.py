"""
Aegis Reasoning Engine Executable Demo
Demonstrates problem decomposition, DecisionGraph DAG sorting, alternative generation, risk estimation, and confidence scoring.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from runtime.src.config import AegisConfig, ReasoningDepth
from runtime.src.reasoning import ReasoningPipeline


def main():
    print("================================================================================")
    print("AEGIS REASONING ENGINE PRODUCTION DEMO")
    print("================================================================================")

    config = AegisConfig.load_from_env()
    pipeline = ReasoningPipeline(config)

    task = "Redesign database pool architecture for high-concurrency microservices"
    print(f"\nTask: {task}")
    print("Executing L3 Deep Reasoning Analysis...\n")

    result = pipeline.run(task, depth=ReasoningDepth.L3_DEEP)

    print("=== DECISION GRAPH TOPOLOGICAL ORDER ===")
    for idx, step_id in enumerate(result.plan.ordered_steps, 1):
        node = result.graph.nodes[step_id]
        print(f"  {idx}. [{node.node_type.value:12s}] {node.node_id:15s} : {node.description}")

    print("\n=== REASONING METRICS ===")
    print(f"  Decomposition Latency : {result.metrics.decomposition_time_ms:.2f} ms")
    print(f"  Total Pipeline Time   : {result.metrics.total_time_ms:.2f} ms")
    print(f"  Node Count            : {result.metrics.node_count}")
    print(f"  Conflict Count        : {result.metrics.conflict_count}")
    print(f"  Token Overhead        : ~{result.metrics.token_overhead} tokens")

    print("\n=== CONFIDENCE & AUDIT ===")
    print(f"  Confidence Score      : {result.confidence_score:.2f} (Threshold: {config.confidence_threshold:.2f})")
    print(f"  Audit Approved        : {'YES' if result.is_approved else 'NO'}")
    if result.review_comments:
        print("  Review Comments       :")
        for c in result.review_comments:
            print(f"    - {c}")

    print("================================================================================")
    print("DEMO COMPLETE — REASONING ENGINE OPERATING AT PRODUCTION RIGOR")
    print("================================================================================")


if __name__ == "__main__":
    main()
