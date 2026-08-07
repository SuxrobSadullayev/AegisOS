"""
Modul 7: ModelGateway (Gemini Provider)
Manages HTTP/REST API communications with Gemini LLM provider endpoints. Supports zero-dependency fallback for offline/mock execution.
"""

import json
import urllib.request
import urllib.error
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from runtime.src.config import AegisConfig


class ModelGatewayInterface(ABC):
    @abstractmethod
    def generate_response(self, system_prompt: str, user_prompt: str) -> str:
        pass


class GeminiModelProvider(ModelGatewayInterface):
    def __init__(self, config: AegisConfig):
        self.config = config

    def generate_response(self, system_prompt: str, user_prompt: str) -> str:
        api_key = self.config.gemini_api_key

        # Offline / Mock Fallback if API key is not set
        if not api_key:
            return self._mock_response(user_prompt)

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.config.gemini_model}:generateContent?key={api_key}"
        payload = {
            "systemInstruction": {
                "parts": [{"text": system_prompt}]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": user_prompt}]
                }
            ]
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"}
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                resp_data = json.loads(resp.read().decode("utf-8"))
                candidates = resp_data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "")
                return "Error: Empty response from Gemini API"
        except urllib.error.HTTPError as e:
            return f"HTTPError from Gemini API: {e.code} - {e.reason}"
        except Exception as e:
            return f"Error connecting to Gemini API: {str(e)}"

    def _mock_response(self, user_prompt: str) -> str:
        return (
            f"[Aegis Runtime Executable — Offline Mode Response]\n"
            f"Analyzed request: {user_prompt}\n"
            f"Status: Executed under Aegis Layer 0 Kernel operating rules."
        )
