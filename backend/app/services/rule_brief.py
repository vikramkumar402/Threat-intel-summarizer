"""Rule-based brief generator used when no LLM provider is configured.

Produces a real, useful daily brief by aggregating the actual scraped intel
items — not a fixed stub. Top CVEs are ranked by KEV membership then CVSS;
threat themes come from keyword frequency over the last 24h corpus.
"""
from __future__ import annotations

import re
from collections import Counter
from typing import Dict, List

CVE_RE = re.compile(r"CVE-\d{4}-\d{4,7}", re.IGNORECASE)
CVSS_RE = re.compile(r"CVSS\s*([0-9]+(?:\.[0-9]+)?)", re.IGNORECASE)

THEME_KEYWORDS: Dict[str, List[str]] = {
    "Ransomware": ["ransomware", "ransom note", "lockbit", "blackcat", "alphv"],
    "Zero-day exploitation": ["zero-day", "zero day", "0-day", "0day"],
    "Critical infrastructure targeting": [
        "critical infrastructure",
        "ics",
        "scada",
        "operational technology",
        "ot network",
        "energy sector",
        "water utility",
    ],
    "Nation-state activity": [
        "nation-state",
        "state-sponsored",
        "apt",
        "north korea",
        "russia",
        "china",
        "iran",
    ],
    "Supply chain compromise": [
        "supply chain",
        "compromised package",
        "package compromise",
        "npm package",
        "pypi",
    ],
    "Phishing & social engineering": ["phishing", "spearphishing", "social engineering"],
    "Edge / VPN exploitation": [
        "vpn",
        "edge device",
        "fortinet",
        "ivanti",
        "citrix",
        "cisco asa",
        "palo alto",
    ],
    "Cloud & identity attacks": [
        "okta",
        "azure ad",
        "entra id",
        "iam policy",
        "cloud bucket",
        "s3 bucket",
    ],
    "Active exploitation in the wild": [
        "actively exploited",
        "exploited in the wild",
        "in-the-wild",
    ],
}

CRITICAL_INFRA_HINTS = [
    "critical infrastructure",
    "ics",
    "scada",
    "energy",
    "water utility",
    "hospital",
    "healthcare",
    "power grid",
]

NATION_STATE_HINTS = ["nation-state", "state-sponsored", "apt", "advanced persistent"]
ZERODAY_HINTS = ["zero-day", "zero day", "0-day", "0day"]


def _extract_cvss(text: str) -> float | None:
    m = CVSS_RE.search(text or "")
    if not m:
        return None
    try:
        return float(m.group(1))
    except ValueError:
        return None


def _extract_cve(text: str) -> str | None:
    m = CVE_RE.search(text or "")
    return m.group(0).upper() if m else None


def _exploitation_status(item: dict) -> str:
    if item.get("source") == "CISA":
        return "in_the_wild"
    text = ((item.get("title") or "") + " " + (item.get("raw_text") or "")).lower()
    if any(h in text for h in ZERODAY_HINTS):
        return "in_the_wild"
    if "exploit" in text or "poc" in text or "proof of concept" in text:
        return "poc_available"
    return "unknown"


def _severity_label(score: float | None, fallback: str | None) -> str:
    if score is not None:
        if score >= 9.0:
            return "CRITICAL"
        if score >= 7.0:
            return "HIGH"
        if score >= 4.0:
            return "MEDIUM"
        if score > 0:
            return "LOW"
    return (fallback or "UNKNOWN").upper()


def _affected(text: str) -> str:
    """Best-effort vendor/product extraction from a CISA-style title."""
    if not text:
        return "various"
    parts = text.split(" - ")
    if len(parts) >= 2:
        return parts[1].strip()
    return parts[0][:80]


def build_top_cves(items: List[dict], limit: int = 5) -> List[dict]:
    candidates: list[tuple[int, float, dict]] = []
    for item in items:
        cve = _extract_cve(item.get("title", "")) or _extract_cve(item.get("raw_text", ""))
        if not cve:
            continue
        cvss = _extract_cvss(item.get("title", "") + " " + (item.get("raw_text") or "")) or 0.0
        # Rank: CISA KEV first, then CVSS desc.
        kev_priority = 1 if item.get("source") == "CISA" else 0
        candidates.append((kev_priority, cvss, {**item, "_cve": cve, "_cvss": cvss}))

    candidates.sort(key=lambda t: (t[0], t[1]), reverse=True)
    seen: set[str] = set()
    top: List[dict] = []
    for _, _, item in candidates:
        cve = item["_cve"]
        if cve in seen:
            continue
        seen.add(cve)
        score = item["_cvss"] if item["_cvss"] > 0 else None
        top.append(
            {
                "cve_id": cve,
                "cvss_score": score if score is not None else 0.0,
                "severity": _severity_label(score, item.get("severity")),
                "affected_products": _affected(item.get("title", "")),
                "exploitation_status": _exploitation_status(item),
                "impact_summary": (item.get("raw_text") or "")[:220].strip(),
            }
        )
        if len(top) >= limit:
            break
    return top


def detect_themes(items: List[dict]) -> List[str]:
    counts: Counter[str] = Counter()
    for item in items:
        text = (
            (item.get("title") or "") + " " + (item.get("raw_text") or "")
        ).lower()
        for theme, kws in THEME_KEYWORDS.items():
            if any(kw in text for kw in kws):
                counts[theme] += 1
    if not counts:
        return ["No dominant themes detected in the last 24h."]
    return [theme for theme, _ in counts.most_common(5)]


def detect_flags(items: List[dict]) -> List[str]:
    flags: List[str] = []
    kev_count = sum(1 for i in items if i.get("source") == "CISA")
    if kev_count:
        flags.append(f"{kev_count} CISA KEV entries (treat as actively exploited)")

    zd = [
        i for i in items
        if any(h in (i.get("title", "") + (i.get("raw_text") or "")).lower() for h in ZERODAY_HINTS)
    ]
    if zd:
        flags.append(f"{len(zd)} zero-day reports")

    ns = [
        i for i in items
        if any(h in (i.get("title", "") + (i.get("raw_text") or "")).lower() for h in NATION_STATE_HINTS)
    ]
    if ns:
        flags.append(f"{len(ns)} items mentioning nation-state activity")

    ci = [
        i for i in items
        if any(h in (i.get("title", "") + (i.get("raw_text") or "")).lower() for h in CRITICAL_INFRA_HINTS)
    ]
    if ci:
        flags.append(f"{len(ci)} items touching critical infrastructure")

    return flags or ["No high-priority flags raised today."]


def severity_distribution(items: List[dict]) -> Dict[str, int]:
    dist = Counter()
    for item in items:
        dist[(item.get("severity") or "UNKNOWN").upper()] += 1
    return dict(dist)


def build_recommendations(top_cves: List[dict], items: List[dict]) -> List[str]:
    recs: List[str] = []

    kev_cves = [c["cve_id"] for c in top_cves if c["exploitation_status"] == "in_the_wild"]
    if kev_cves:
        recs.append(
            "Patch CISA KEV entries immediately, prioritising "
            + ", ".join(kev_cves[:3])
            + " — these have confirmed in-the-wild exploitation."
        )
    else:
        recs.append(
            "No KEV entries today — use the window to validate patch baselines on internet-exposed services."
        )

    crit_count = sum(1 for c in top_cves if c["severity"] == "CRITICAL")
    if crit_count:
        recs.append(
            f"Schedule emergency change windows for the {crit_count} CRITICAL CVEs above; "
            "block exploit traffic at WAF/IPS as a compensating control until patched."
        )

    sources = {i.get("source") for i in items}
    if "CISA" in sources or "NVD" in sources:
        recs.append(
            "Ingest today's CVE list into your vulnerability scanner and re-run targeted scans on production assets."
        )

    recs.append(
        "Hunt for the IOCs extracted from today's intel (IPs, domains, hashes) across EDR and DNS logs."
    )
    recs.append(
        "Brief the SOC on the threat themes above and update detection rules where the theme touches your stack."
    )
    return recs[:5]


def build_executive_summary(
    items: List[dict], top_cves: List[dict], themes: List[str], flags: List[str]
) -> str:
    sources = sorted({i.get("source", "?") for i in items if i.get("source")})
    dist = severity_distribution(items)
    crit = dist.get("CRITICAL", 0)
    high = dist.get("HIGH", 0)
    kev_count = sum(1 for i in items if i.get("source") == "CISA")

    lead = (
        f"Today's brief covers {len(items)} items collected from {len(sources)} sources "
        f"({', '.join(sources)})."
    )
    severity_line = (
        f" Severity breakdown: {crit} CRITICAL / {high} HIGH; "
        f"{kev_count} entries from CISA KEV."
    )
    cve_line = (
        f" Highest-priority vulnerabilities: {', '.join(c['cve_id'] for c in top_cves[:3])}."
        if top_cves
        else ""
    )
    theme_line = f" Dominant themes: {'; '.join(themes[:3])}." if themes else ""
    flag_line = f" Notable flags: {flags[0]}." if flags and "No high" not in flags[0] else ""
    return lead + severity_line + cve_line + theme_line + flag_line


def generate(items: List[dict]) -> dict:
    """Produce a full brief payload from the items list."""
    top_cves = build_top_cves(items)
    themes = detect_themes(items)
    flags = detect_flags(items)
    recs = build_recommendations(top_cves, items)
    summary = build_executive_summary(items, top_cves, themes, flags)
    return {
        "executive_summary": summary,
        "top_cves": top_cves,
        "threat_themes": themes,
        "high_priority_flags": flags,
        "recommendations": recs,
        "_telemetry": {
            "input_tokens": 0,
            "output_tokens": 0,
            "cost_usd": 0.0,
            "prompt_version": "rule-based-v1",
        },
    }
