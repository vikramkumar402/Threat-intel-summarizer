"""LLM service for threat intelligence analysis using local/Bedrock/Groq providers."""
from __future__ import annotations

import asyncio
import json
import random
from pathlib import Path
from typing import Dict, List

import httpx
import structlog

from app.config import get_settings

logger = structlog.get_logger()

PROMPT_VERSION = "v2"
PROMPT_FILE = f"daily_brief_{PROMPT_VERSION}.txt"

# Bedrock Claude Sonnet pricing (USD per 1K tokens, approximate).
INPUT_COST_PER_1K = 0.003
OUTPUT_COST_PER_1K = 0.015


class LLMService:
    """Service for LLM-based threat intelligence analysis."""

    def __init__(self) -> None:
        self.settings = get_settings()
        requested_provider = self.settings.llm_provider_normalized
        self.provider = requested_provider
        if requested_provider == "bedrock" and not self.settings.aws_configured:
            logger.warning(
                "llm_provider_fallback",
                requested=requested_provider,
                selected="local",
                reason="aws_not_configured",
            )
            self.provider = "local"
        if requested_provider == "groq" and not self.settings.groq_api_key:
            logger.warning(
                "llm_provider_fallback",
                requested=requested_provider,
                selected="local",
                reason="groq_api_key_missing",
            )
            self.provider = "local"
        self.model_id = self.settings.bedrock_model_id
        self.groq_model = self.settings.groq_model
        self.prompt_template = self._load_prompt_template()
        self._client = None

    @property
    def client(self):
        if self._client is None and self.provider == "bedrock":
            import boto3

            self._client = boto3.client(
                "bedrock-runtime",
                aws_access_key_id=self.settings.aws_access_key_id,
                aws_secret_access_key=self.settings.aws_secret_access_key,
                region_name=self.settings.aws_region,
            )
        return self._client

    def _load_prompt_template(self) -> str:
        path = Path(__file__).parent.parent / "prompts" / PROMPT_FILE
        if not path.exists():
            path = Path(__file__).parent.parent / "prompts" / "daily_brief.txt"
        return path.read_text()

    async def generate_daily_brief(self, intel_items: List[Dict]) -> Dict:
        """Generate a structured daily brief from raw intel.

        Returns a dict including parsed brief fields + token/cost telemetry.
        """
        if self.provider == "local":
            return self._local_brief(intel_items)

        if self.provider == "groq":
            prepared = self._prepare_items_for_prompt(intel_items, max_items=12, max_raw_chars=280)
        else:
            prepared = self._prepare_items_for_prompt(intel_items, max_items=60, max_raw_chars=1500)

        raw_intel = self._format_intel_items(prepared)
        if self.provider == "groq":
            raw_intel = raw_intel[:12000]
        prompt = self.prompt_template.replace("{raw_intel}", raw_intel)

        result = await self._invoke_with_retries(prompt)
        return result

    async def _invoke_with_retries(self, prompt: str) -> Dict:
        last_exc: Exception | None = None
        for attempt in range(4):
            try:
                return await asyncio.to_thread(self._invoke_blocking, prompt)
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                backoff = (2**attempt) + random.random()
                logger.warning(
                    "llm_invoke_failed",
                    provider=self.provider,
                    attempt=attempt + 1,
                    backoff_s=round(backoff, 2),
                    error=str(exc),
                )
                await asyncio.sleep(backoff)
        assert last_exc is not None
        raise last_exc

    def _invoke_blocking(self, prompt: str) -> Dict:
        if self.provider == "groq":
            return self._invoke_groq(prompt)

        return self._invoke_bedrock(prompt)

    def _invoke_bedrock(self, prompt: str) -> Dict:
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4096,
            "temperature": 0.2,
            "messages": [{"role": "user", "content": prompt}],
        }
        response = self.client.invoke_model(
            modelId=self.model_id, body=json.dumps(request_body)
        )
        body = json.loads(response["body"].read())
        content_blocks = body.get("content", [])
        text = "".join(b.get("text", "") for b in content_blocks if b.get("type") == "text")

        usage = body.get("usage", {})
        input_tokens = int(usage.get("input_tokens", 0))
        output_tokens = int(usage.get("output_tokens", 0))
        cost = (input_tokens / 1000.0) * INPUT_COST_PER_1K + (
            output_tokens / 1000.0
        ) * OUTPUT_COST_PER_1K

        parsed = self._parse_json_payload(text)
        parsed["_telemetry"] = {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": round(cost, 6),
            "prompt_version": PROMPT_VERSION,
            "provider": "bedrock",
        }
        return parsed

    def _invoke_groq(self, prompt: str) -> Dict:
        assert self.settings.groq_api_key is not None
        payload = {
            "model": self.groq_model,
            "temperature": 0.2,
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"},
        }
        headers = {
            "Authorization": f"Bearer {self.settings.groq_api_key}",
            "Content-Type": "application/json",
        }
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            body = response.json()

        choices = body.get("choices") or []
        text = ""
        if choices:
            message = choices[0].get("message") or {}
            text = message.get("content") or ""

        usage = body.get("usage") or {}
        input_tokens = int(usage.get("prompt_tokens") or 0)
        output_tokens = int(usage.get("completion_tokens") or 0)

        parsed = self._parse_json_payload(text)
        parsed["_telemetry"] = {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": 0.0,
            "prompt_version": PROMPT_VERSION,
            "provider": "groq",
            "model": self.groq_model,
        }
        return parsed

    @staticmethod
    def _parse_json_payload(text: str) -> Dict:
        text = text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        if "```json" in text:
            chunk = text.split("```json", 1)[1].split("```", 1)[0].strip()
            return json.loads(chunk)
        if "```" in text:
            chunk = text.split("```", 1)[1].split("```", 1)[0].strip()
            return json.loads(chunk)
        # Last resort: try to find the outermost JSON object.
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start : end + 1])
        raise ValueError("Could not parse LLM response as JSON")

    @staticmethod
    def _format_intel_items(items: List[Dict]) -> str:
        formatted = []
        for item in items:
            formatted.append(
                f"Source: {item.get('source')}\n"
                f"Title: {item.get('title')}\n"
                f"Severity: {item.get('severity')}\n"
                f"Published: {item.get('published_at') or ''}\n"
                f"Content: {item.get('raw_text') or ''}\n"
                f"URL: {item.get('url')}\n"
                f"---"
            )
        return "\n\n".join(formatted)

    @staticmethod
    def _prepare_items_for_prompt(
        items: List[Dict], max_items: int, max_raw_chars: int
    ) -> List[Dict]:
        """Cap payload size to avoid provider request limits."""
        prepared: List[Dict] = []
        for item in items[:max_items]:
            trimmed = dict(item)
            raw_text = str(trimmed.get("raw_text") or "")
            trimmed["raw_text"] = raw_text[:max_raw_chars]
            prepared.append(trimmed)
        return prepared

    @staticmethod
    def _local_brief(items: List[Dict]) -> Dict:
        """Rule-based brief used by the free local provider."""
        from app.services import rule_brief

        return rule_brief.generate(items)
