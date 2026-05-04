"""IOC (indicator-of-compromise) extraction utilities."""
from __future__ import annotations

import ipaddress
import re
from typing import Dict, List

CVE_RE = re.compile(r"CVE-\d{4}-\d{4,7}", re.IGNORECASE)
SHA256_RE = re.compile(r"\b[a-fA-F0-9]{64}\b")
SHA1_RE = re.compile(r"\b[a-fA-F0-9]{40}\b")
MD5_RE = re.compile(r"\b[a-fA-F0-9]{32}\b")
IPV4_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
DOMAIN_RE = re.compile(
    r"\b(?=[a-zA-Z0-9-]{1,63}\.)(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\b"
)
URL_RE = re.compile(r"https?://[^\s)]+", re.IGNORECASE)
EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")

# Filter common domains that pollute results.
DOMAIN_DENYLIST = {
    "github.com",
    "twitter.com",
    "google.com",
    "microsoft.com",
    "example.com",
}


def _valid_ipv4(value: str) -> bool:
    try:
        addr = ipaddress.ip_address(value)
    except ValueError:
        return False
    return not (addr.is_loopback or addr.is_private or addr.is_multicast or addr.is_unspecified)


def extract(text: str) -> List[Dict[str, str]]:
    """Return de-duplicated IOC dicts: {type, value}."""
    if not text:
        return []
    found: List[Dict[str, str]] = []
    seen: set[tuple[str, str]] = set()

    def add(kind: str, value: str) -> None:
        key = (kind, value.lower())
        if key in seen:
            return
        seen.add(key)
        found.append({"type": kind, "value": value})

    for match in CVE_RE.findall(text):
        add("cve", match.upper())
    for match in URL_RE.findall(text):
        add("url", match.rstrip(".,);"))
    for match in EMAIL_RE.findall(text):
        add("email", match)
    for match in SHA256_RE.findall(text):
        add("sha256", match.lower())
    for match in SHA1_RE.findall(text):
        # Avoid double-counting SHA1 substrings of SHA256.
        if not any(match.lower() in existing["value"] for existing in found if existing["type"] == "sha256"):
            add("sha1", match.lower())
    for match in MD5_RE.findall(text):
        if not any(match.lower() in existing["value"] for existing in found if existing["type"] in {"sha1", "sha256"}):
            add("md5", match.lower())
    for match in IPV4_RE.findall(text):
        if _valid_ipv4(match):
            add("ipv4", match)
    for match in DOMAIN_RE.findall(text):
        lower = match.lower()
        if lower in DOMAIN_DENYLIST or lower.endswith(".png") or lower.endswith(".jpg"):
            continue
        add("domain", lower)

    return found
