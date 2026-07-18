"""LLM backends: Ollama (primary), Hugging Face Inference API, offline rules."""

from __future__ import annotations

import logging
import os
import re
from abc import ABC, abstractmethod
from typing import Any

import requests

from ai_gov_map.ingest.models import RegulationRecord

from .prompt import SYSTEM_PROMPT, build_user_prompt, parse_model_response, truncate_words

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
OLLAMA_MODELS = ("llama3.1:8b", "mistral:7b", "llama3.1", "mistral")

# Small open instruct model that works on the free HF Inference API when a token is set.
HF_DEFAULT_MODEL = os.environ.get(
    "HF_SUMMARISE_MODEL",
    "HuggingFaceH4/zephyr-7b-beta",
)
HF_API_URL = os.environ.get(
    "HF_API_URL",
    f"https://api-inference.huggingface.co/models/{HF_DEFAULT_MODEL}",
)


class BackendError(RuntimeError):
    """Raised when a preferred backend cannot serve a request."""


class SummariseBackend(ABC):
    name: str = "base"

    @abstractmethod
    def summarise(self, record: RegulationRecord) -> dict[str, Any]:
        """Return parsed fields: summary, risk_tier, rationale, needs_review, confidence, model."""


def _hf_token() -> str | None:
    return os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_API_TOKEN") or None


def ollama_available(
    *,
    base_url: str = OLLAMA_BASE_URL,
    session: requests.Session | None = None,
    timeout: float = 2.0,
) -> bool:
    sess = session or requests.Session()
    try:
        resp = sess.get(f"{base_url}/api/tags", timeout=timeout)
        return resp.status_code == 200
    except requests.RequestException:
        return False


def pick_ollama_model(
    *,
    base_url: str = OLLAMA_BASE_URL,
    preferred: tuple[str, ...] = OLLAMA_MODELS,
    session: requests.Session | None = None,
    timeout: float = 5.0,
) -> str | None:
    sess = session or requests.Session()
    try:
        resp = sess.get(f"{base_url}/api/tags", timeout=timeout)
        resp.raise_for_status()
        names = {m.get("name", "") for m in resp.json().get("models", [])}
    except (requests.RequestException, ValueError, KeyError):
        return None
    for cand in preferred:
        if cand in names:
            return cand
        # Match tags like llama3.1:8b-instruct-q4_0
        for name in names:
            if name == cand or name.startswith(cand.split(":")[0]):
                if cand in name or name.split(":")[0] == cand.split(":")[0]:
                    return name
    return next(iter(names), None) if names else None


class OllamaBackend(SummariseBackend):
    name = "ollama"

    def __init__(
        self,
        *,
        base_url: str = OLLAMA_BASE_URL,
        model: str | None = None,
        session: requests.Session | None = None,
        timeout: float = 120.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.session = session or requests.Session()
        self.timeout = timeout
        self.model = model or pick_ollama_model(base_url=self.base_url, session=self.session)
        if not self.model:
            raise BackendError(
                f"Ollama is unreachable or has no models at {self.base_url}. "
                "Install Ollama and pull e.g. `ollama pull llama3.1:8b` or `ollama pull mistral:7b`."
            )

    def summarise(self, record: RegulationRecord) -> dict[str, Any]:
        user = build_user_prompt(
            title=record.title,
            source=record.source,
            jurisdiction=record.jurisdiction,
            text_excerpt=record.text_excerpt,
            url=record.url,
        )
        payload = {
            "model": self.model,
            "stream": False,
            "prompt": f"{SYSTEM_PROMPT}\n\n{user}\n\nJSON:",
            "options": {"temperature": 0.2},
        }
        try:
            resp = self.session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            text = str(data.get("response") or "")
        except requests.RequestException as exc:
            raise BackendError(f"Ollama generate failed ({self.model}): {exc}") from exc
        parsed = parse_model_response(text)
        parsed["model"] = f"ollama:{self.model}"
        return parsed


class HuggingFaceBackend(SummariseBackend):
    name = "hf"

    def __init__(
        self,
        *,
        api_url: str = HF_API_URL,
        model: str = HF_DEFAULT_MODEL,
        token: str | None = None,
        session: requests.Session | None = None,
        timeout: float = 120.0,
    ) -> None:
        self.api_url = api_url
        self.model = model
        self.token = token if token is not None else _hf_token()
        self.session = session or requests.Session()
        self.timeout = timeout
        if not self.token:
            raise BackendError(
                "Hugging Face token missing. Set HF_TOKEN or HUGGINGFACE_API_TOKEN "
                "for the free Inference API fallback."
            )

    def summarise(self, record: RegulationRecord) -> dict[str, Any]:
        user = build_user_prompt(
            title=record.title,
            source=record.source,
            jurisdiction=record.jurisdiction,
            text_excerpt=record.text_excerpt,
            url=record.url,
        )
        # Zephyr / Mistral-style chat prompt
        prompt = (
            f"<|system|>\n{SYSTEM_PROMPT}</s>\n"
            f"<|user|>\n{user}</s>\n"
            f"<|assistant|>\n"
        )
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 400,
                "temperature": 0.2,
                "return_full_text": False,
            },
        }
        try:
            resp = self.session.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=self.timeout,
            )
            if resp.status_code == 503:
                raise BackendError(
                    f"HF model {self.model} is loading (503). Retry shortly."
                )
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as exc:
            raise BackendError(f"HF Inference API failed ({self.model}): {exc}") from exc

        text = ""
        if isinstance(data, list) and data:
            text = str(data[0].get("generated_text") or "")
        elif isinstance(data, dict):
            text = str(data.get("generated_text") or data.get("summary_text") or "")
        parsed = parse_model_response(text)
        parsed["model"] = f"hf:{self.model}"
        return parsed


# Keyword heuristics for deterministic offline / CI / Streamlit Cloud demos.
_UNACCEPTABLE = re.compile(
    r"\b(social\s+scor|subliminal|real[- ]?time\s+remote\s+biometric|"
    r"manipulat(?:e|ion)\s+behav|banned\s+ai|prohibited\s+ai)\b",
    re.I,
)
_HIGH = re.compile(
    r"\b(high[- ]?risk|annex\s*iii|employment|hiring|credit\s+scor|"
    r"biometric|law\s+enforcement|critical\s+infrastructure|medical\s+device|"
    r"ai\s+act|regulation\s*\(eu\)\s*2024/1689|sanzion|sanction|"
    r"emotion|stress\s+dei\s+dipendent|workplace|lavoro|"
    r"minori|minors|character\.ai|verifica\s+dell.?et)\b",
    re.I,
)
_LIMITED = re.compile(
    r"\b(chatbot|deepfake|transparency|trasparenza|disclosure|"
    r"emotion\s+recognition|synthetic\s+media|label(?:l)?ing)\b",
    re.I,
)


def rule_based_tier(record: RegulationRecord) -> tuple[str, str, float]:
    """Return (tier, rationale, confidence) from title/excerpt keywords."""
    blob = f"{record.title}\n{record.text_excerpt}\n{record.source}"
    if _UNACCEPTABLE.search(blob):
        return (
            "unacceptable",
            "Keyword signals match prohibited / social-scoring style practices.",
            0.55,
        )
    if record.source == "EUR-Lex" or re.search(r"32024R1689|AI Act|regulatory framework", blob, re.I):
        return (
            "high",
            "Official EU AI Act / regulatory-framework material — treated as high-risk corpus context.",
            0.6,
        )
    if _HIGH.search(blob):
        return (
            "high",
            "Title/excerpt mentions high-risk domains (enforcement, biometrics, employment, sanctions).",
            0.55,
        )
    if _LIMITED.search(blob):
        return (
            "limited",
            "Signals point to transparency / limited-risk disclosure obligations.",
            0.5,
        )
    return (
        "minimal",
        "General governance, strategy, or institutional news without clear high-risk product duties.",
        0.45,
    )


def rule_based_summary(record: RegulationRecord) -> str:
    title = (record.title or "Untitled item").strip()
    jur = record.jurisdiction or "unspecified jurisdiction"
    src = record.source or "unknown source"
    excerpt = (record.text_excerpt or "").strip()
    if excerpt:
        # First ~40 words of excerpt as colour
        snippet = " ".join(excerpt.split()[:40])
        if len(excerpt.split()) > 40:
            snippet += "…"
        body = (
            f"{title} ({src}, {jur}). "
            f"This feed item notes: {snippet} "
            f"It is recorded for Italy/EU AI governance monitoring; "
            f"risk tagging uses offline heuristics when no LLM is available."
        )
    else:
        body = (
            f"{title} ({src}, {jur}). "
            f"No excerpt was available. Tagged offline for the compliance monitor demo."
        )
    return truncate_words(body, 120)


class OfflineBackend(SummariseBackend):
    """Deterministic stub — CI, Streamlit Cloud, and machines without Ollama/HF."""

    name = "offline"

    def summarise(self, record: RegulationRecord) -> dict[str, Any]:
        tier, rationale, confidence = rule_based_tier(record)
        return {
            "summary": rule_based_summary(record),
            "risk_tier": tier,
            "rationale": rationale,
            "needs_review": True,  # offline always eligible for Phase 4 review
            "confidence": confidence,
            "model": "offline:rules-v1",
        }


def resolve_backend(
    preference: str = "auto",
    *,
    session: requests.Session | None = None,
    ollama_model: str | None = None,
) -> SummariseBackend:
    """Select backend: auto → ollama → hf → offline."""
    pref = (preference or "auto").lower().strip()
    sess = session or requests.Session()

    def try_ollama() -> SummariseBackend | None:
        try:
            return OllamaBackend(session=sess, model=ollama_model)
        except BackendError as exc:
            logger.info("Ollama unavailable: %s", exc)
            return None

    def try_hf() -> SummariseBackend | None:
        try:
            return HuggingFaceBackend(session=sess)
        except BackendError as exc:
            logger.info("HF unavailable: %s", exc)
            return None

    if pref == "offline":
        return OfflineBackend()
    if pref == "ollama":
        backend = try_ollama()
        if backend is None:
            raise BackendError(
                "Ollama backend requested but unavailable at "
                f"{OLLAMA_BASE_URL}. Start Ollama or use --backend offline|hf|auto."
            )
        return backend
    if pref == "hf":
        backend = try_hf()
        if backend is None:
            raise BackendError(
                "HF backend requested but HF_TOKEN / HUGGINGFACE_API_TOKEN is unset "
                "or the API is unreachable."
            )
        return backend

    # auto
    backend = try_ollama()
    if backend:
        return backend
    backend = try_hf()
    if backend:
        return backend
    logger.warning(
        "Neither Ollama nor Hugging Face available; using offline rule-based summaries. "
        "Prefer committing data/summaries.jsonl so Streamlit Cloud needs no LLM secrets."
    )
    return OfflineBackend()
