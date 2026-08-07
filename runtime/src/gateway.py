"""
Aegis AI Operating System — ModelGateway
Production-grade multi-provider gateway supporting Gemini, Claude, OpenAI, OpenRouter, and Mock providers.
Features: Common Interface, Streaming, Exponential Backoff Retry, Timeouts, Rate Limit Handling, Error Recovery, and Token Counting.
"""

import os
import json
import time
import math
import random
import urllib.request
import urllib.error
import ssl
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Generator, Any
from runtime.src.config import AegisConfig


@dataclass
class ModelResponse:
    """Canonical Model Response Container."""
    text: str
    token_count: int
    latency_ms: float
    provider: str
    model: str
    finish_reason: str = "STOP"
    raw_response: Optional[Dict[str, Any]] = None


class ModelGatewayInterface(ABC):
    """Common Interface for all Aegis Model Providers."""

    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str) -> ModelResponse:
        """Executes a synchronous request to the model provider."""
        pass

    @abstractmethod
    def generate_stream(self, system_prompt: str, user_prompt: str) -> Generator[str, None, ModelResponse]:
        """Streams text chunks from the model provider."""
        pass

    def estimate_tokens(self, text: str) -> int:
        """Estimates token count for text using standard word/character ratio heuristics."""
        if not text:
            return 0
        words = len(text.split())
        chars = len(text)
        return int(max(words * 1.3, chars / 4.0))


class MockProvider(ModelGatewayInterface):
    """Mock Provider for deterministic offline testing and fallbacks."""

    def __init__(self, config: AegisConfig, simulate_delay_ms: float = 10.0, simulate_error: bool = False):
        self.config = config
        self.simulate_delay_ms = simulate_delay_ms
        self.simulate_error = simulate_error

    def generate(self, system_prompt: str, user_prompt: str) -> ModelResponse:
        start_time = time.time()
        if self.simulate_error:
            raise RuntimeError("MockProvider simulated failure")

        time.sleep(self.simulate_delay_ms / 1000.0)
        text = (
            f"[Aegis Mock Provider Output]\n"
            f"Analyzed Request: {user_prompt}\n"
            f"Status: Executed under Aegis Layer 0 Kernel operating rules."
        )
        latency = (time.time() - start_time) * 1000.0
        tokens = self.estimate_tokens(text)

        return ModelResponse(
            text=text,
            token_count=tokens,
            latency_ms=round(latency, 2),
            provider="mock",
            model="mock-v1",
            finish_reason="STOP"
        )

    def generate_stream(self, system_prompt: str, user_prompt: str) -> Generator[str, None, ModelResponse]:
        start_time = time.time()
        if self.simulate_error:
            raise RuntimeError("MockProvider simulated streaming failure")

        full_text = (
            f"[Aegis Mock Provider Stream]\n"
            f"Task: {user_prompt}\n"
            f"Kernel Operating Status: Active."
        )
        chunks = full_text.split(" ")

        for chunk in chunks:
            time.sleep(0.01)
            yield chunk + " "

        latency = (time.time() - start_time) * 1000.0
        tokens = self.estimate_tokens(full_text)

        return ModelResponse(
            text=full_text,
            token_count=tokens,
            latency_ms=round(latency, 2),
            provider="mock",
            model="mock-v1",
            finish_reason="STOP"
        )


class BaseHTTPProvider(ModelGatewayInterface):
    """Base HTTP Provider with exponential backoff, retry, and rate-limit handling."""

    def __init__(self, config: AegisConfig, provider_name: str, default_model: str):
        self.config = config
        self.provider_name = provider_name
        self.default_model = default_model
        self.timeout = 30.0

    def _execute_http_request_with_retry(self, url: str, headers: Dict[str, str], payload: Dict[str, Any]) -> Dict[str, Any]:
        data = json.dumps(payload).encode("utf-8")
        retries = 0
        max_retries = self.config.max_retries
        backoff = 1.0

        ctx = ssl.create_default_context()

        while retries <= max_retries:
            req = urllib.request.Request(url, data=data, headers=headers, method="POST")
            try:
                with urllib.request.urlopen(req, timeout=self.timeout, context=ctx) as resp:
                    resp_bytes = resp.read()
                    return json.loads(resp_bytes.decode("utf-8"))
            except urllib.error.HTTPError as e:
                status = e.code
                error_body = e.read().decode("utf-8", errors="ignore")

                # Handle Rate Limits (429) or Server Errors (5xx) with backoff
                if status in (429, 500, 502, 503, 504) and retries < max_retries:
                    retries += 1
                    sleep_time = backoff * (2 ** (retries - 1)) + random.uniform(0.1, 0.5)
                    time.sleep(sleep_time)
                    continue
                else:
                    raise RuntimeError(f"{self.provider_name} API HTTP Error {status}: {error_body}")
            except (urllib.error.URLError, TimeoutError) as e:
                if retries < max_retries:
                    retries += 1
                    sleep_time = backoff * (2 ** (retries - 1)) + random.uniform(0.1, 0.5)
                    time.sleep(sleep_time)
                    continue
                else:
                    raise RuntimeError(f"{self.provider_name} Connection Timeout/Error: {str(e)}")

        raise RuntimeError(f"{self.provider_name} Max Retries Exceeded ({max_retries})")


class GeminiProvider(BaseHTTPProvider):
    """Google Gemini REST API Provider."""

    def __init__(self, config: AegisConfig):
        super().__init__(config, "Gemini", config.gemini_model or "gemini-1.5-pro")

    def generate(self, system_prompt: str, user_prompt: str) -> ModelResponse:
        start_time = time.time()
        api_key = self.config.gemini_api_key

        if not api_key:
            # Fall back to mock if API key is not configured
            return MockProvider(self.config).generate(system_prompt, user_prompt)

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.default_model}:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": user_prompt}]}]
        }

        resp_json = self._execute_http_request_with_retry(url, headers, payload)
        text = ""
        candidates = resp_json.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            if parts:
                text = parts[0].get("text", "")

        if not text:
            raise ValueError("Gemini API returned an empty response candidate")

        latency = (time.time() - start_time) * 1000.0
        tokens = self.estimate_tokens(text)

        return ModelResponse(
            text=text,
            token_count=tokens,
            latency_ms=round(latency, 2),
            provider="gemini",
            model=self.default_model,
            finish_reason="STOP",
            raw_response=resp_json
        )

    def generate_stream(self, system_prompt: str, user_prompt: str) -> Generator[str, None, ModelResponse]:
        # Synchronous fallback streaming wrapper for REST
        resp = self.generate(system_prompt, user_prompt)
        words = resp.text.split(" ")
        for word in words:
            yield word + " "
        return resp


class ClaudeProvider(BaseHTTPProvider):
    """Anthropic Claude Messages API Provider."""

    def __init__(self, config: AegisConfig, api_key: str = "", model: str = "claude-3-5-sonnet-20241022"):
        super().__init__(config, "Claude", model)
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")

    def generate(self, system_prompt: str, user_prompt: str) -> ModelResponse:
        start_time = time.time()
        if not self.api_key:
            return MockProvider(self.config).generate(system_prompt, user_prompt)

        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01"
        }
        payload = {
            "model": self.default_model,
            "max_tokens": 4096,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}]
        }

        resp_json = self._execute_http_request_with_retry(url, headers, payload)
        text = ""
        contents = resp_json.get("content", [])
        if contents:
            text = contents[0].get("text", "")

        latency = (time.time() - start_time) * 1000.0
        tokens = self.estimate_tokens(text)

        return ModelResponse(
            text=text,
            token_count=tokens,
            latency_ms=round(latency, 2),
            provider="claude",
            model=self.default_model,
            finish_reason="STOP",
            raw_response=resp_json
        )

    def generate_stream(self, system_prompt: str, user_prompt: str) -> Generator[str, None, ModelResponse]:
        resp = self.generate(system_prompt, user_prompt)
        words = resp.text.split(" ")
        for word in words:
            yield word + " "
        return resp


class OpenAIProvider(BaseHTTPProvider):
    """OpenAI Chat Completions API Provider."""

    def __init__(self, config: AegisConfig, api_key: str = "", model: str = "gpt-4o"):
        super().__init__(config, "OpenAI", model)
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")

    def generate(self, system_prompt: str, user_prompt: str) -> ModelResponse:
        start_time = time.time()
        if not self.api_key:
            return MockProvider(self.config).generate(system_prompt, user_prompt)

        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        payload = {
            "model": self.default_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        }

        resp_json = self._execute_http_request_with_retry(url, headers, payload)
        text = ""
        choices = resp_json.get("choices", [])
        if choices:
            text = choices[0].get("message", {}).get("content", "")

        latency = (time.time() - start_time) * 1000.0
        tokens = self.estimate_tokens(text)

        return ModelResponse(
            text=text,
            token_count=tokens,
            latency_ms=round(latency, 2),
            provider="openai",
            model=self.default_model,
            finish_reason="STOP",
            raw_response=resp_json
        )

    def generate_stream(self, system_prompt: str, user_prompt: str) -> Generator[str, None, ModelResponse]:
        resp = self.generate(system_prompt, user_prompt)
        words = resp.text.split(" ")
        for word in words:
            yield word + " "
        return resp


class OpenRouterProvider(BaseHTTPProvider):
    """OpenRouter Unified API Provider."""

    def __init__(self, config: AegisConfig, api_key: str = "", model: str = "anthropic/claude-3.5-sonnet"):
        super().__init__(config, "OpenRouter", model)
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY", "")

    def generate(self, system_prompt: str, user_prompt: str) -> ModelResponse:
        start_time = time.time()
        if not self.api_key:
            return MockProvider(self.config).generate(system_prompt, user_prompt)

        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://aegis.dev",
            "X-Title": "Aegis AI Operating System"
        }
        payload = {
            "model": self.default_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        }

        resp_json = self._execute_http_request_with_retry(url, headers, payload)
        text = ""
        choices = resp_json.get("choices", [])
        if choices:
            text = choices[0].get("message", {}).get("content", "")

        latency = (time.time() - start_time) * 1000.0
        tokens = self.estimate_tokens(text)

        return ModelResponse(
            text=text,
            token_count=tokens,
            latency_ms=round(latency, 2),
            provider="openrouter",
            model=self.default_model,
            finish_reason="STOP",
            raw_response=resp_json
        )

    def generate_stream(self, system_prompt: str, user_prompt: str) -> Generator[str, None, ModelResponse]:
        resp = self.generate(system_prompt, user_prompt)
        words = resp.text.split(" ")
        for word in words:
            yield word + " "
        return resp


class ModelGatewayFactory:
    """Factory router for instantiating model providers with plugin extension support."""

    _custom_providers: Dict[str, Callable[[AegisConfig], ModelGatewayInterface]] = {}

    @classmethod
    def register_provider(cls, provider_name: str, factory_fn: Callable[[AegisConfig], ModelGatewayInterface]) -> None:
        """Plugins can register custom model providers."""
        cls._custom_providers[provider_name.lower().strip()] = factory_fn

    @classmethod
    def get_provider(cls, provider_name: str, config: AegisConfig) -> ModelGatewayInterface:
        p = provider_name.lower().strip()
        if p in cls._custom_providers:
            return cls._custom_providers[p](config)

        if p == "gemini":
            return GeminiProvider(config)
        elif p == "claude":
            return ClaudeProvider(config)
        elif p == "openai":
            return OpenAIProvider(config)
        elif p == "openrouter":
            return OpenRouterProvider(config)
        elif p == "mock":
            return MockProvider(config)
        else:
            raise ValueError(f"Unsupported model provider: '{provider_name}'")

