"""Severity normalization across heterogeneous sources."""
from __future__ import annotations

from typing import Optional

CRITICAL = "CRITICAL"
HIGH = "HIGH"
MEDIUM = "MEDIUM"
LOW = "LOW"
UNKNOWN = "UNKNOWN"

ORDER = {LOW: 1, MEDIUM: 2, HIGH: 3, CRITICAL: 4, UNKNOWN: 0}


def from_cvss(score: Optional[float]) -> str:
    if score is None:
        return UNKNOWN
    if score >= 9.0:
        return CRITICAL
    if score >= 7.0:
        return HIGH
    if score >= 4.0:
        return MEDIUM
    if score > 0:
        return LOW
    return UNKNOWN


def from_source_signal(source: str, raw_severity: Optional[str]) -> str:
    """Override per-source heuristics. CISA KEV is always CRITICAL."""
    if source == "CISA":
        return CRITICAL
    if source == "US-CERT":
        return HIGH
    return (raw_severity or UNKNOWN).upper()


def meets_threshold(severity: str, threshold: str) -> bool:
    return ORDER.get((severity or UNKNOWN).upper(), 0) >= ORDER.get(
        (threshold or LOW).upper(), 1
    )
