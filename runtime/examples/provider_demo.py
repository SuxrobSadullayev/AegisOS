"""
Aegis AI Operating System — Model Gateway Provider Switching Demo
Demonstrates dynamic LLM provider selection (Mock, Gemini, Claude, OpenAI, OpenRouter)
and safe credential failure handling without secret leaks.
"""

from runtime.src.config import AegisConfig
from runtime.src.gateway import ModelGatewayFactory, MockProvider


def main():
    print("🛡️ Aegis Model Gateway Provider Switching Demo")
    config = AegisConfig.load()

    providers = ["mock", "gemini", "claude", "openai", "openrouter"]

    for prov in providers:
        print(f"\n--- Initializing Provider: {prov.upper()} ---")
        try:
            gateway = ModelGatewayFactory.get_provider(prov, config)
            print(f"✅ Successfully initialized provider: {gateway.__class__.__name__}")
            if isinstance(gateway, MockProvider):
                resp = gateway.generate("System prompt", "Test user prompt for " + prov)
                print(f"   Output: {resp.text[:60]}...")
        except Exception as err:
            print(f"❌ Handled expected credential / configuration error: {err}")

    print("\n✅ Model Gateway Provider Switching Demo completed successfully.")


if __name__ == "__main__":
    main()
