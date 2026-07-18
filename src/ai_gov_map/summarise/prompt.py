"""Prompt construction and response normalisation for risk tagging."""

from __future__ import annotations

import json
import re
from typing import Any

from .models import RISK_TIERS

_MAX_SUMMARY_WORDS = 120

SYSTEM_PROMPT = """You are an EU AI Act triage assistant for a compliance monitor.
Given a regulatory/policy document, produce:
1) a plain-language summary of at most 120 words,
2) exactly one risk_tier from this closed list: unacceptable, high, limited, minimal,
3) a short rationale (1–2 sentences) explaining the tier.

Rules for risk_tier (EU AI Act style):
- unacceptable: banned practices (social scoring, subliminal manipulation, real-time remote biometric ID in public for law enforcement, etc.)
- high: high-risk Annex III / safety-critical / employment, credit, education, biometric ID, critical infrastructure, medical devices
- limited: transparency obligations (chatbots, deepfakes, emotion recognition disclosure)
- minimal: general governance news, strategy, webinars, soft policy without clear high-risk product obligations

Respond with ONLY a single JSON object, no markdown:
{"summary":"...","risk_tier":"high","rationale":"..."}
"""


def build_user_prompt(
    *,
    title: str,
    source: str,
    jurisdiction: str,
    text_excerpt: str,
    url: str = "",
) -> str:
    excerpt = (text_excerpt or "").strip()
    if len(excerpt) > 2000:
        excerpt = excerpt[:2000] + "…"
    parts = [
        f"Title: {title or '(untitled)'}",
        f"Source: {source or '(unknown)'}",
        f"Jurisdiction: {jurisdiction or '(unknown)'}",
    ]
    if url:
        parts.append(f"URL: {url}")
    parts.append(f"Excerpt:\n{excerpt or '(none)'}")
    return "\n".join(parts)


def truncate_words(text: str, max_words: int = _MAX_SUMMARY_WORDS) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text.strip()
    return " ".join(words[:max_words]).rstrip(",.;:") + "…"


def normalise_risk_tier(raw: str | None) -> str | None:
    """Map free-text model output onto the closed taxonomy, or None if unknown."""
    if not raw:
        return None
    cleaned = raw.strip().lower().replace("_", " ").replace("-", " ")
    cleaned = re.sub(r"[^a-z\s]", "", cleaned).strip()
    # Direct match
    for tier in RISK_TIERS:
        if cleaned == tier or cleaned == f"{tier} risk":
            return tier
    # Common aliases
    aliases = {
        "unacceptable risk": "unacceptable",
        "prohibited": "unacceptable",
        "banned": "unacceptable",
        "high risk": "high",
        "limited risk": "limited",
        "transparency": "limited",
        "minimal risk": "minimal",
        "low": "minimal",
        "low risk": "minimal",
        "no risk": "minimal",
    }
    if cleaned in aliases:
        return aliases[cleaned]
    # Substring fallback (prefer longer / more specific first)
    for tier in ("unacceptable", "limited", "minimal", "high"):
        if tier in cleaned:
            return tier
    return None


def _extract_json_object(text: str) -> dict[str, Any] | None:
    text = text.strip()
    if not text:
        return None
    # Strip common markdown fences
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL | re.IGNORECASE)
    if fence:
        text = fence.group(1)
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return obj
    except json.JSONDecodeError:
        pass
    # Find first {...} blob
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        try:
            obj = json.loads(text[start : end + 1])
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            return None
    return None


def parse_model_response(text: str) -> dict[str, Any]:
    """Parse model text into summary / risk_tier / rationale + review flags.

    Returns dict with keys: summary, risk_tier, rationale, needs_review, confidence.
    Invalid or missing risk_tier → needs_review=True and risk_tier='minimal' placeholder.
    """
    obj = _extract_json_object(text) or {}
    summary = str(obj.get("summary") or "").strip()
    rationale = str(obj.get("rationale") or obj.get("reason") or "").strip()
    raw_tier = obj.get("risk_tier") or obj.get("risk") or obj.get("tier")
    if not isinstance(raw_tier, str):
        raw_tier = str(raw_tier) if raw_tier is not None else ""

    # Heuristic fallback if model returned prose instead of JSON
    if not summary and text.strip():
        summary = truncate_words(re.sub(r"\s+", " ", text.strip()), _MAX_SUMMARY_WORDS)

    tier = normalise_risk_tier(raw_tier)
    needs_review = False
    confidence = 0.75

    if tier is None:
        # Try to find a tier mention in free text
        tier = normalise_risk_tier(text)
    if tier is None:
        tier = "minimal"
        needs_review = True
        confidence = 0.2
        if not rationale:
            rationale = "Model did not return a valid risk_tier from the closed taxonomy."
    elif raw_tier.strip().lower() not in RISK_TIERS and raw_tier.strip():
        # Normalised from alias — flag soft uncertainty
        needs_review = True
        confidence = 0.55

    summary = truncate_words(summary or "No summary produced.", _MAX_SUMMARY_WORDS)
    if not rationale:
        rationale = f"Assigned EU AI Act–style tier '{tier}' from available document text."
        needs_review = True
        confidence = min(confidence, 0.45)

    return {
        "summary": summary,
        "risk_tier": tier,
        "rationale": rationale.strip(),
        "needs_review": needs_review,
        "confidence": confidence,
    }
