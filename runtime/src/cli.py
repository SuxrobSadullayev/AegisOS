"""
Modul 9: CLI & Runtime Executable Entrypoint
Main command-line entrypoint for the Aegis Executable Runtime Engine.
"""

import sys
import argparse
from runtime.src.config import AegisConfig
from runtime.src.epistemic import EpistemicGraphStore
from runtime.src.resolver import ContextResolver
from runtime.src.pipeline import EnginePipeline
from runtime.src.composer import PromptComposer
from runtime.src.gateway import GeminiModelProvider
from runtime.src.quality import QualityPipeline


def main():
    parser = argparse.ArgumentParser(description="Aegis AI Operating System Executable Runtime Engine")
    parser.add_argument("--task", "-t", required=True, help="Task description or prompt for Aegis")
    parser.add_argument("--depth", "-d", choices=["L1", "L2", "L3"], help="Override reasoning depth level")
    parser.add_argument("--model", "-m", help="Override target LLM model")
    args = parser.parse_args()

    config = AegisConfig.load_from_env()
    if args.model:
        config.gemini_model = args.model

    print(f"🛡️ Aegis AI OS Runtime Engine v2.0.0 [Target: {config.gemini_model}]")
    print(f"Task: {args.task}\n")

    # 1. Initialize Memory Store & Resolver
    store = EpistemicGraphStore()
    resolver = ContextResolver()

    # 2. Resolve Context & Task Intent
    resolved_ctx = resolver.resolve(args.task)
    print(f"✓ Resolved Reasoning Depth: {resolved_ctx.reasoning_depth.value}")
    if resolved_ctx.target_modules:
        print(f"✓ Resolved Domain Modules: {', '.join(resolved_ctx.target_modules)}")

    # 3. Execute Engine Pipeline
    pipeline = EnginePipeline(config, store)
    trace = pipeline.execute(args.task, resolved_ctx)
    print(f"✓ Engine Pipeline Execution: Confidence Score = {trace.confidence_score:.2f} (Gate: {'PASS' if trace.gate_passed else 'FAIL'})")

    if not trace.gate_passed:
        print("❌ Execution halted: Confidence score below minimum threshold (0.70)", file=sys.stderr)
        sys.exit(1)

    # 4. Compose System Prompt Payload
    composer = PromptComposer(config)
    system_prompt = composer.compose(resolved_ctx, trace)

    # 5. Dispatch to Model Gateway
    gateway = GeminiModelProvider(config)
    print("✓ Dispatching to Gemini Provider...")
    initial_response = gateway.generate_response(system_prompt, args.task)

    # 6. Quality Pipeline & Auto-Refinement
    quality_pipeline = QualityPipeline(config, gateway)
    result = quality_pipeline.validate_and_refine(system_prompt, args.task, initial_response)

    print(f"✓ Quality Pipeline Result: Status = {result.status.value} (Retries: {result.retry_count})\n")
    print("================================================================================")
    print(result.refined_response)
    print("================================================================================")


if __name__ == "__main__":
    main()
