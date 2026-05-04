"""Lightweight MITRE ATT&CK keyword → technique tagger.

This is a deliberately small, hand-curated map. It is meant to surface
plausible techniques for analysts to confirm — not to be authoritative.
"""
from __future__ import annotations

from typing import Dict, List

TECHNIQUE_MAP: Dict[str, List[str]] = {
    "T1566": ["phishing", "spearphishing", "email lure"],
    "T1190": ["public-facing", "exposed", "internet-facing", "rce in"],
    "T1486": ["ransomware", "encrypted files", "ransom note"],
    "T1059": ["powershell", "command shell", "bash script"],
    "T1071": ["c2", "command and control", "beacon"],
    "T1078": ["valid accounts", "stolen credentials", "credential reuse"],
    "T1499": ["denial of service", "ddos", "dos attack"],
    "T1133": ["vpn exploit", "remote services", "rdp"],
    "T1195": ["supply chain", "compromised dependency", "package compromise"],
    "T1611": ["container escape", "kubernetes privilege"],
}


def tag(text: str) -> List[str]:
    if not text:
        return []
    lower = text.lower()
    techniques: List[str] = []
    for tid, kws in TECHNIQUE_MAP.items():
        if any(kw in lower for kw in kws):
            techniques.append(tid)
    return sorted(set(techniques))
