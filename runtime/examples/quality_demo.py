"""
Aegis Quality Engine Production CLI Demo
Demonstrates 12 quality validation gates, issue reporting, and the automated Auto-Repair loop.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from runtime.src.config import AegisConfig
from runtime.src.gateway import MockProvider
from runtime.src.quality import QualityPipeline, QualityContext


def main():
    print("================================================================================")
    print("AEGIS QUALITY ENGINE PRODUCTION DEMO")
    print("================================================================================")

    config = AegisConfig.load_from_env()
    gateway = MockProvider(config)
    pipeline = QualityPipeline(config, gateway)

    print("\n1. Validating Clean Response...")
    clean_text = "This is a production-grade response generated in accordance with Aegis Kernel rules."
    ctx1 = QualityContext("System", "Task", clean_text, config)
    report1 = pipeline.validate(ctx1)
    print(f"   Status : {report1.result.status.value}")
    print(f"   Score  : {report1.result.score}")
    print(f"   Time   : {report1.metrics.validation_time_ms:.2f} ms")

    print("\n2. Validating Response with Quality Gate Failures...")
    dirty_text = "Here is the code with API_KEY='secret123' and unclosed ``` code block"
    ctx2 = QualityContext("System", "Task", dirty_text, config)
    report2 = pipeline.validate(ctx2)
    print(f"   Status : {report2.result.status.value}")
    print(f"   Issues Found: {report2.metrics.issues_found_count}")
    for issue in report2.result.issues:
        print(f"    - [{issue.severity.value}] Gate: {issue.rule.value} — {issue.description}")

    print("\n3. Executing Auto-Repair Loop...")
    repair_res = pipeline.validate_and_refine("System", "Task", dirty_text)
    print(f"   Repaired Successfully : {repair_res.is_repaired}")
    print(f"   Attempts Used         : {repair_res.attempts_used}")
    print(f"   Refined Text Snippet  : {repair_res.repaired_text[:100]}...")

    print("================================================================================")
    print("DEMO COMPLETE — QUALITY ENGINE OPERATING AT PRODUCTION RIGOR")
    print("================================================================================")


if __name__ == "__main__":
    main()
