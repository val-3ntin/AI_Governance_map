"""Taxonomy term expansions for AI use-cases and sectors (rules-based)."""

from __future__ import annotations

# Map entity.ai_use_cases → additional search phrases (lowercased at match time).
USE_CASE_TERMS: dict[str, tuple[str, ...]] = {
    "clinical_decision_support": (
        "clinical decision",
        "clinical",
        "diagnosis",
        "sanità",
        "sanita",
        "healthcare",
        "medical",
    ),
    "medical_imaging": (
        "medical imaging",
        "radiology",
        "imaging",
        "medical device",
        "medical devices",
    ),
    "recruitment_screening": (
        "recruitment",
        "hiring",
        "cv screening",
        "employment",
        "lavoro",
        "hr",
    ),
    "employee_monitoring": (
        "employee monitoring",
        "workplace",
        "lavoro",
        "employment",
    ),
    "biometric_identification": (
        "biometric",
        "biometrics",
        "remote biometric",
        "identification",
    ),
    "facial_recognition": (
        "facial recognition",
        "face recognition",
        "biometric",
    ),
    "credit_scoring": (
        "credit scor",
        "credit scoring",
        "credit",
        "lending",
        "banking",
    ),
    "fraud_detection": (
        "fraud",
        "data breach",
        "security incident",
    ),
    "public_service_chatbot": (
        "chatbot",
        "public service",
        "public administration",
        "agid",
        "pa digitale",
    ),
    "benefits_eligibility": (
        "benefits",
        "eligibility",
        "public administration",
        "welfare",
    ),
    "student_assessment": (
        "assessment",
        "scuola",
        "school",
        "education",
        "students",
        "minori",
        "minors",
    ),
    "adaptive_learning": (
        "adaptive learning",
        "learning",
        "education",
        "academy",
        "scuola",
    ),
    "industrial_quality_control": (
        "quality control",
        "industrial",
        "manufacturing",
        "machine vision",
    ),
    "predictive_maintenance": (
        "predictive maintenance",
        "maintenance",
        "industrial",
        "critical infrastructure",
    ),
    "regulatory_monitoring": (
        "ai act",
        "artificial intelligence",
        "intelligenza artificiale",
        "governance",
        "regulatory framework",
        "oecd.ai",
        "32024r1689",
    ),
    "conformity_assessment_support": (
        "conformity",
        "high-risk",
        "annex iii",
        "regulation (eu) 2024/1689",
        "ai act",
    ),
}

# Sector → soft expansion terms (lower weight than keywords / use-cases).
SECTOR_TERMS: dict[str, tuple[str, ...]] = {
    "healthcare": ("healthcare", "sanità", "sanita", "medical", "health", "ausl"),
    "hr_recruitment": ("recruitment", "hiring", "employment", "lavoro", "hr"),
    "biometrics": ("biometric", "biometrics", "facial recognition", "privacy"),
    "finance": ("finance", "financial", "credit", "banking", "fraud"),
    "public_admin": (
        "public administration",
        "agid",
        "government",
        "pubblica amministrazione",
    ),
    "education": ("education", "scuola", "school", "students", "minori", "minors"),
    "industrial_sme": ("industrial", "manufacturing", "sme", "pmi", "sicurezza"),
    "compliance_advisory": (
        "ai act",
        "governance",
        "regulatory framework",
        "artificial intelligence",
        "intelligenza artificiale",
    ),
}

# Risk-tier boost when entity.risk_exposure aligns with summary tier.
RISK_ALIGNMENT_BOOST: dict[str, float] = {
    "unacceptable": 0.5,
    "high": 0.35,
    "limited": 0.15,
    "minimal": 0.0,
}
