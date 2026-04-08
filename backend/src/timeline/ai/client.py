"""
AI Client with auto-detection of Ollama or LM Studio.

Falls back gracefully — the rest of the app works without any AI backend.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod

import httpx

from timeline.config import settings

logger = logging.getLogger(__name__)


class AIBackend(ABC):
    name: str

    @abstractmethod
    async def is_available(self) -> bool: ...

    @abstractmethod
    async def embed(self, text: str) -> list[float] | None: ...

    @abstractmethod
    async def generate(self, prompt: str) -> str | None: ...


class OllamaBackend(AIBackend):
    name = "ollama"

    def __init__(self):
        self._available: bool | None = None

    async def is_available(self) -> bool:
        if self._available is not None:
            return self._available
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                r = await client.get(f"{settings.ollama_url}/api/tags")
                self._available = r.status_code == 200
        except Exception:
            self._available = False
        return self._available

    async def embed(self, text: str) -> list[float] | None:
        if not await self.is_available():
            return None
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                r = await client.post(
                    f"{settings.ollama_url}/api/embeddings",
                    json={"model": settings.ollama_embed_model, "prompt": text},
                )
                return r.json().get("embedding")
        except Exception as e:
            logger.warning("Ollama embed failed: %s", e)
            return None

    async def generate(self, prompt: str) -> str | None:
        if not await self.is_available():
            return None
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                r = await client.post(
                    f"{settings.ollama_url}/api/generate",
                    json={"model": settings.ollama_llm_model, "prompt": prompt, "stream": False},
                )
                return r.json().get("response")
        except Exception as e:
            logger.warning("Ollama generate failed: %s", e)
            return None


class LMStudioBackend(AIBackend):
    name = "lmstudio"

    def __init__(self):
        self._available: bool | None = None

    async def is_available(self) -> bool:
        if self._available is not None:
            return self._available
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                r = await client.get(f"{settings.lmstudio_url}/models")
                self._available = r.status_code == 200
        except Exception:
            self._available = False
        return self._available

    async def embed(self, text: str) -> list[float] | None:
        if not await self.is_available():
            return None
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                r = await client.post(
                    f"{settings.lmstudio_url}/embeddings",
                    json={"model": settings.lmstudio_embed_model, "input": text},
                )
                data = r.json()
                return data["data"][0]["embedding"]
        except Exception as e:
            logger.warning("LM Studio embed failed: %s", e)
            return None

    async def generate(self, prompt: str) -> str | None:
        if not await self.is_available():
            return None
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                r = await client.post(
                    f"{settings.lmstudio_url}/chat/completions",
                    json={
                        "model": settings.lmstudio_llm_model,
                        "messages": [{"role": "user", "content": prompt}],
                        "stream": False,
                    },
                )
                return r.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.warning("LM Studio generate failed: %s", e)
            return None


class NoAIBackend(AIBackend):
    name = "none"

    async def is_available(self) -> bool:
        return False

    async def embed(self, text: str) -> list[float] | None:
        return None

    async def generate(self, prompt: str) -> str | None:
        return None


_active_backend: AIBackend | None = None


async def get_backend() -> AIBackend:
    global _active_backend
    if _active_backend is not None:
        return _active_backend

    preferred = settings.ai_backend.lower()

    if preferred == "ollama":
        b = OllamaBackend()
        if await b.is_available():
            _active_backend = b
            logger.info("AI backend: Ollama")
            return b
    elif preferred == "lmstudio":
        b = LMStudioBackend()
        if await b.is_available():
            _active_backend = b
            logger.info("AI backend: LM Studio")
            return b
    else:  # auto
        for cls in [OllamaBackend, LMStudioBackend]:
            b = cls()
            if await b.is_available():
                _active_backend = b
                logger.info("AI backend: %s (auto-detected)", b.name)
                return b

    _active_backend = NoAIBackend()
    logger.info("No AI backend available — AI features disabled")
    return _active_backend


def reset_backend():
    """Call this to re-detect backend (e.g. after config change)."""
    global _active_backend
    _active_backend = None
