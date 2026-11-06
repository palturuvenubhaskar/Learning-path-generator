"""
OpenRouter model catalog.

The model list changes often, so it is fetched live and only free models are
offered. A small fallback list keeps the UI usable if the network is down.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import httpx

from config import OPENROUTER_MODELS_URL


@dataclass(frozen=True)
class ModelOption:
    id: str
    name: str
    context_length: int = 0
    free: bool = True

    @property
    def label(self) -> str:
        if self.context_length:
            return f"{self.name} · {self.context_length // 1000}k ctx"
        return self.name


# Used only when the catalog cannot be fetched. These ids may age out.
FALLBACK_FREE_MODELS: List[ModelOption] = [
    ModelOption("deepseek/deepseek-chat-v3.1:free", "DeepSeek Chat v3.1 (free)"),
    ModelOption("meta-llama/llama-3.3-70b-instruct:free", "Llama 3.3 70B (free)"),
    ModelOption("qwen/qwen3-235b-a22b:free", "Qwen3 235B (free)"),
    ModelOption("mistralai/mistral-small-3.2-24b-instruct:free", "Mistral Small 3.2 (free)"),
]


def _as_float(value: Any) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def is_free_model(entry: Dict[str, Any]) -> bool:
    """Free means every listed price is zero, not just the two token prices.

    Music and image models can report zero token prices while charging per clip.
    """
    pricing = entry.get("pricing") or {}
    if not isinstance(pricing, dict) or not pricing:
        # No pricing block at all: trust the :free suffix only.
        return str(entry.get("id", "")).endswith(":free")

    for key, raw in pricing.items():
        amount = _as_float(raw)
        if amount is not None and amount > 0:
            return False

    prompt = _as_float(pricing.get("prompt"))
    completion = _as_float(pricing.get("completion"))
    if prompt != 0.0 or completion != 0.0:
        return str(entry.get("id", "")).endswith(":free")
    return True


def is_text_chat_model(entry: Dict[str, Any]) -> bool:
    """Reject audio, image and music models: they cannot produce a plan."""
    architecture = entry.get("architecture")
    if not isinstance(architecture, dict):
        return True
    outputs = architecture.get("output_modalities")
    if not isinstance(outputs, list) or not outputs:
        modality = str(architecture.get("modality") or "")
        if "->" in modality:
            outputs = [part.strip() for part in modality.split("->", 1)[1].split("+")]
        else:
            return True
    return all(str(item).lower() == "text" for item in outputs)


def parse_models(payload: Dict[str, Any]) -> List[ModelOption]:
    """Turn an OpenRouter /models response into free chat ModelOptions."""
    entries = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(entries, list):
        return []

    options: List[ModelOption] = []
    seen = set()
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        if not is_text_chat_model(entry) or not is_free_model(entry):
            continue
        model_id = str(entry.get("id", "")).strip()
        if not model_id or model_id in seen:
            continue
        seen.add(model_id)
        context = entry.get("context_length") or entry.get("top_provider", {}).get("context_length") or 0
        try:
            context = int(context)
        except (TypeError, ValueError):
            context = 0
        name = str(entry.get("name") or model_id)
        options.append(ModelOption(model_id, name, context, True))

    options.sort(key=lambda option: (-option.context_length, option.name.lower()))
    return options


# Families that reliably emit long structured JSON on the free tier.
TRUSTED_FAMILIES = (
    "deepseek",
    "qwen",
    "llama",
    "mistral",
    "nemotron",
    "gpt-oss",
    "glm",
    "gemma",
    "phi-",
    "command",
)
NOISY_MARKERS = ("stealth", "cloak", "anonymous", "experimental", "preview", "alpha", "beta")


def _model_score(model: ModelOption) -> tuple:
    """Lower is better: trusted family first, then fewer warning markers, then size."""
    lowered = model.id.lower()
    trusted = any(family in lowered for family in TRUSTED_FAMILIES)
    noisy = sum(1 for marker in NOISY_MARKERS if marker in lowered)
    # A very small context window cannot hold a 30-day plan.
    too_small = model.context_length and model.context_length < 32000
    return (not trusted, noisy, bool(too_small), -min(model.context_length, 400000))


def recommended_default(models: List[ModelOption]) -> Optional[ModelOption]:
    """Best guess for a model that can return a long JSON plan in one shot."""
    if not models:
        return None
    return min(models, key=_model_score)


def list_free_models(
    api_key: Optional[str] = None,
    timeout: float = 10.0,
) -> List[ModelOption]:
    """Fetch the live free-model catalog, falling back to a static list."""
    headers = {"Accept": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    try:
        response = httpx.get(OPENROUTER_MODELS_URL, headers=headers, timeout=timeout)
        response.raise_for_status()
        models = parse_models(response.json())
        return models or FALLBACK_FREE_MODELS
    except Exception:
        return FALLBACK_FREE_MODELS
