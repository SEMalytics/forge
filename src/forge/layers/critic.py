"""
Multi-LLM Adversarial Critic — KF 7.26

Runs the same adversarial critique prompt across multiple LLMs.
Findings confirmed by ≥2 models are tagged [cross-model confirmed] and surfaced first.

Models:
  - Claude (primary, always runs via ANTHROPIC_API_KEY)
  - OpenAI/Codex (secondary, runs when OPENAI_API_KEY is set)
  - Gemini (optional, runs when GEMINI_API_KEY is set)
"""

import asyncio
import json
import os
import re
from dataclasses import dataclass, field
from typing import List, Optional

from forge.utils.errors import ForgeError
from forge.utils.logger import logger


ADVERSARIAL_PROMPT = """\
You are an adversarial code reviewer. Your core assumption: there is at least one significant flaw in the content below. Your job is to find it — not decide whether one exists.

Follow this 5-step protocol:
1. Adversarial entry — adopt the perspective of someone who must make this fail. What's the first move?
2. High-value targets — which components, if broken, cause the most damage? Start there.
3. Compound failure search — what two-component failure isn't handled? What race condition exists?
4. Assumption inversion — pick the 2-3 most load-bearing assumptions. Invert each. What breaks?
5. Report — output ONLY Sev 1 (Critical) and Sev 2 (High) findings. Suppress Low and Medium.

Severity reference:
  Sev 1 = Critical: production failure, data loss, security breach
  Sev 2 = High: significant degradation; architectural change needed

Output your findings as a JSON array. Each finding must have these exact keys:
  - "description": one sentence describing the flaw
  - "severity": integer 1 or 2
  - "severity_label": "Critical" or "High"
  - "location": file/function/component where the flaw exists, or "general" if not specific

Example output:
[
  {{"description": "Token refresh is not thread-safe; concurrent requests cause double-issue.", "severity": 1, "severity_label": "Critical", "location": "auth/refresh.py"}},
  {{"description": "No retry budget cap; upstream failure causes infinite loop.", "severity": 2, "severity_label": "High", "location": "client.py:retry_loop"}}
]

If you find zero Sev 1-2 findings, return an empty array: []

Now review this content:

{context_block}{content}"""


class CriticError(ForgeError):
    """Errors during adversarial critique"""
    pass


@dataclass
class Finding:
    description: str
    severity: int  # 1=Critical, 2=High
    severity_label: str
    location: str
    model_sources: List[str] = field(default_factory=list)

    @property
    def is_confirmed(self) -> bool:
        return len(self.model_sources) >= 2

    @property
    def tag(self) -> str:
        return "[cross-model confirmed]" if self.is_confirmed else "[single-model]"

    def to_dict(self) -> dict:
        return {
            "description": self.description,
            "severity": self.severity,
            "severity_label": self.severity_label,
            "location": self.location,
            "model_sources": self.model_sources,
            "confirmed": self.is_confirmed,
            "tag": self.tag,
        }


@dataclass
class CritiqueResult:
    findings: List[Finding]
    models_used: List[str]
    confirmed_count: int
    single_model_count: int

    def to_dict(self) -> dict:
        return {
            "models_used": self.models_used,
            "confirmed_count": self.confirmed_count,
            "single_model_count": self.single_model_count,
            "findings": [f.to_dict() for f in self.findings],
        }

    def format_report(self) -> str:
        lines = ["## Adversarial Critic Report\n"]
        lines.append(f"Models: {', '.join(self.models_used)}\n")

        confirmed = [f for f in self.findings if f.is_confirmed]
        single = [f for f in self.findings if not f.is_confirmed]

        if len(self.models_used) > 1 and confirmed:
            lines.append("### Cross-Model Confirmed")
            for f in confirmed:
                lines.append(
                    f"- {f.description} "
                    f"[{f.severity_label}] [cross-model confirmed] — {f.location}"
                )
            lines.append("")

        if single:
            lines.append("### Single-Model Findings")
            for f in single:
                lines.append(
                    f"- {f.description} "
                    f"[{f.severity_label}] [single-model: {', '.join(f.model_sources)}] — {f.location}"
                )
            lines.append("")

        if not self.findings:
            lines.append("No Sev 1-2 findings detected across all models.\n")

        if self.findings:
            top = self.findings[0]
            lines.append("### Recommended Revision")
            lines.append(
                f"Address [{top.severity_label}]: {top.description} (at {top.location})"
            )

        return "\n".join(lines)


def _build_prompt(content: str, context: str = "") -> str:
    context_block = f"Context:\n{context}\n\n" if context.strip() else ""
    return ADVERSARIAL_PROMPT.format(context_block=context_block, content=content)


def _parse_findings(raw: str, model_name: str) -> List[Finding]:
    """Extract JSON array of findings from model output."""
    # Try to locate a JSON array in the response
    match = re.search(r"\[.*?\]", raw, re.DOTALL)
    if not match:
        logger.warning(f"{model_name}: no JSON array found in response")
        return []

    try:
        items = json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        logger.warning(f"{model_name}: JSON parse error — {exc}")
        return []

    findings = []
    for item in items:
        try:
            sev = int(item.get("severity", 2))
            if sev not in (1, 2):
                continue
            findings.append(Finding(
                description=str(item.get("description", "")).strip(),
                severity=sev,
                severity_label=item.get("severity_label", "High"),
                location=str(item.get("location", "general")).strip(),
                model_sources=[model_name],
            ))
        except (KeyError, ValueError, TypeError) as exc:
            logger.debug(f"{model_name}: skipped malformed finding — {exc}")

    return findings


def _merge_findings(all_findings: List[Finding]) -> List[Finding]:
    """
    Merge findings across models.

    Two findings are considered the same if their descriptions share
    a significant keyword overlap (Jaccard similarity ≥ 0.35) or if
    the same location is flagged at the same severity.
    """
    merged: List[Finding] = []

    def _tokens(text: str) -> set:
        return {w.lower() for w in re.findall(r"[a-z]+", text) if len(w) > 3}

    def _similar(a: Finding, b: Finding) -> bool:
        # Same location + severity is a strong signal
        if (a.location == b.location and a.severity == b.severity
                and a.location != "general"):
            return True
        ta, tb = _tokens(a.description), _tokens(b.description)
        union = ta | tb
        if not union:
            return False
        return len(ta & tb) / len(union) >= 0.35

    for finding in all_findings:
        matched = None
        for existing in merged:
            if _similar(finding, existing):
                matched = existing
                break
        if matched:
            for src in finding.model_sources:
                if src not in matched.model_sources:
                    matched.model_sources.append(src)
        else:
            merged.append(finding)

    # Sort: confirmed first, then by severity (1 before 2)
    merged.sort(key=lambda f: (0 if f.is_confirmed else 1, f.severity))
    return merged


async def _run_claude(prompt: str, api_key: str) -> List[Finding]:
    from anthropic import Anthropic
    client = Anthropic(api_key=api_key)
    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2048,
            temperature=1,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text
        findings = _parse_findings(raw, "claude")
        logger.info(f"Claude adversarial critic: {len(findings)} findings")
        return findings
    except Exception as exc:
        logger.error(f"Claude critic failed: {exc}")
        return []


async def _run_openai(prompt: str, api_key: str) -> List[Finding]:
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=api_key)
        response = await client.chat.completions.create(
            model="gpt-4o",
            temperature=1,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.choices[0].message.content or ""
        findings = _parse_findings(raw, "openai")
        logger.info(f"OpenAI adversarial critic: {len(findings)} findings")
        return findings
    except ImportError:
        logger.warning("openai package not installed; skipping OpenAI critic")
        return []
    except Exception as exc:
        logger.error(f"OpenAI critic failed: {exc}")
        return []


async def _run_gemini(prompt: str, api_key: str) -> List[Finding]:
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-pro")
        response = await asyncio.to_thread(model.generate_content, prompt)
        raw = response.text or ""
        findings = _parse_findings(raw, "gemini")
        logger.info(f"Gemini adversarial critic: {len(findings)} findings")
        return findings
    except ImportError:
        logger.warning("google-generativeai package not installed; skipping Gemini critic")
        return []
    except Exception as exc:
        logger.error(f"Gemini critic failed: {exc}")
        return []


class MultiLLMCritic:
    """
    KF 7.26 Adversarial Critic with multi-LLM cross-confirmation.

    Claude always runs (ANTHROPIC_API_KEY required).
    OpenAI runs when OPENAI_API_KEY is set.
    Gemini runs when GEMINI_API_KEY is set.

    Findings present in ≥2 models are tagged [cross-model confirmed].
    """

    def __init__(
        self,
        anthropic_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        gemini_api_key: Optional[str] = None,
    ):
        self.anthropic_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY", "")
        self.openai_key = openai_api_key or os.getenv("OPENAI_API_KEY", "")
        self.gemini_key = gemini_api_key or os.getenv("GEMINI_API_KEY", "")

        if not self.anthropic_key:
            raise CriticError("ANTHROPIC_API_KEY is required for the adversarial critic")

    @property
    def active_models(self) -> List[str]:
        models = ["claude"]
        if self.openai_key:
            models.append("openai")
        if self.gemini_key:
            models.append("gemini")
        return models

    async def critique(self, content: str, context: str = "") -> CritiqueResult:
        """
        Run adversarial critique across all available models.

        Args:
            content: The artifact to critique (code, spec, plan, etc.)
            context: Optional context about the artifact's purpose or environment

        Returns:
            CritiqueResult with merged, deduplicated, and ranked findings
        """
        prompt = _build_prompt(content, context)
        logger.info(
            f"Running adversarial critic across models: {', '.join(self.active_models)}"
        )

        # Run all models in parallel
        tasks = [_run_claude(prompt, self.anthropic_key)]
        if self.openai_key:
            tasks.append(_run_openai(prompt, self.openai_key))
        if self.gemini_key:
            tasks.append(_run_gemini(prompt, self.gemini_key))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_findings: List[Finding] = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Critic task exception: {result}")
            elif isinstance(result, list):
                all_findings.extend(result)

        merged = _merge_findings(all_findings)
        confirmed = [f for f in merged if f.is_confirmed]
        single = [f for f in merged if not f.is_confirmed]

        logger.info(
            f"Adversarial critic complete: {len(confirmed)} confirmed, "
            f"{len(single)} single-model findings"
        )

        return CritiqueResult(
            findings=merged,
            models_used=self.active_models,
            confirmed_count=len(confirmed),
            single_model_count=len(single),
        )

    def critique_sync(self, content: str, context: str = "") -> CritiqueResult:
        """Synchronous wrapper for critique()."""
        return asyncio.run(self.critique(content, context))
