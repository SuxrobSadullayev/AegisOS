"""
Aegis ModelGateway CLI Demo
Demonstrates multi-provider routing (Gemini, Claude, OpenAI, OpenRouter, Mock) and streaming responses.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from runtime.src.config import AegisConfig
from runtime.src.gateway import ModelGatewayFactory


def main():
    print("================================================================================")
    print("AEGIS MODELGATEWAY MULTI-PROVIDER CLI DEMO")
    print("================================================================================")

    config = AegisConfig.load_from_env()
    providers = ["mock", "gemini", "claude", "openai", "openrouter"]

    system_prompt = "# AEGIS KERNEL CONTEXT\nMust optimize for correctness over confidence."
    user_prompt = "Refactor database connection pool with thread-safe mutex"

    for p_name in providers:
        print(f"\n--- Provider: {p_name.upper()} ---")
        provider = ModelGatewayFactory.get_provider(p_name, config)

        print("Executing Synchronous Generation...")
        resp = provider.generate(system_prompt, user_prompt)
        print(f"Provider: {resp.provider} | Model: {resp.model} | Latency: {resp.latency_ms}ms | Tokens: {resp.token_count}")
        print(f"Response:\n{resp.text[:120]}...\n")

        print("Executing Streaming Generation...")
        stream = provider.generate_stream(system_prompt, user_prompt)
        print("Stream Output: ", end="", flush=True)
        for chunk in stream:
            print(chunk, end="", flush=True)
        print("\n")

    print("================================================================================")
    print("DEMO COMPLETE — ALL PROVIDERS INTEGRATED SUCCESSFULLY")
    print("================================================================================")


if __name__ == "__main__":
    main()
