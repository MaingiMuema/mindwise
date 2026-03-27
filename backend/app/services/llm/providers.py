from dataclasses import dataclass
from typing import Any

import httpx

from app.core.config import get_settings
from app.core.exceptions import ExternalServiceError


@dataclass(slots=True)
class ProviderSelection:
    name: str
    cost_tier: str
    image_capable: bool
    available: bool


class BaseLLMProvider:
    name = "base"
    cost_tier = "standard"
    image_capable = False

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def generate_json(self, *, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        raise NotImplementedError


class HeuristicProvider(BaseLLMProvider):
    name = "heuristic"
    cost_tier = "free"
    image_capable = False

    @property
    def available(self) -> bool:
        return True

    def generate_json(self, *, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        return {
            "mode": "heuristic",
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
        }


class OpenRouterProvider(BaseLLMProvider):
    name = "openrouter"
    cost_tier = "low"

    def generate_json(self, *, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        if not self.api_key:
            raise ExternalServiceError("OPENROUTER_API_KEY is not configured.")
        response = httpx.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": "openai/gpt-4o-mini",
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            },
            timeout=45.0,
        )
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        return httpx.Response(200, text=content).json()


class GeminiProvider(BaseLLMProvider):
    name = "gemini"
    cost_tier = "low"
    image_capable = True

    def generate_json(self, *, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        if not self.api_key:
            raise ExternalServiceError("GEMINI_API_KEY is not configured.")
        response = httpx.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={self.api_key}",
            json={
                "contents": [
                    {
                        "parts": [
                            {"text": system_prompt},
                            {"text": user_prompt},
                        ]
                    }
                ],
                "generationConfig": {"responseMimeType": "application/json"},
            },
            timeout=45.0,
        )
        response.raise_for_status()
        data = response.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return httpx.Response(200, text=text).json()


class LLMRegistry:
    def __init__(self) -> None:
        settings = get_settings()
        self.providers = {
            "heuristic": HeuristicProvider(),
            "openrouter": OpenRouterProvider(settings.openrouter_api_key),
            "gemini": GeminiProvider(settings.gemini_api_key),
        }

    def choose(self, requested: str | None = None) -> BaseLLMProvider:
        if requested and requested in self.providers and self.providers[requested].available:
            return self.providers[requested]

        settings = get_settings()
        primary = settings.llm_primary_provider
        if primary in self.providers and self.providers[primary].available:
            return self.providers[primary]

        for provider in self.providers.values():
            if provider.available:
                return provider
        return self.providers["heuristic"]

    def selections(self) -> list[ProviderSelection]:
        return [
            ProviderSelection(
                name=provider.name,
                cost_tier=provider.cost_tier,
                image_capable=provider.image_capable,
                available=provider.available,
            )
            for provider in self.providers.values()
        ]
