"""
LLM client — wraps Anthropic Claude to analyse Jenkins build data.
Uses prompt caching to reduce costs on repeated system-prompt calls.
"""

import logging
from dataclasses import dataclass
from typing import Optional

import anthropic

from config import settings
from analyzer.prompts import (
    SYSTEM_PROMPT,
    FAILURE_ANALYSIS_PROMPT,
    QUICK_SUMMARY_PROMPT,
    FLAKY_TEST_PROMPT,
    BUILD_TREND_PROMPT,
    COMPARE_BUILDS_PROMPT,
)
from jenkins.client import BuildInfo

logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    job_name: str
    build_number: int
    result: str
    analysis: str           # Markdown text from the LLM
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cached_tokens: int = 0


def _duration_str(ms: int) -> str:
    if ms <= 0:
        return "unknown"
    secs = ms // 1000
    mins, secs = divmod(secs, 60)
    return f"{mins}m {secs}s" if mins else f"{secs}s"


class LLMAnalyzer:
    """Send Jenkins build data to Claude and return structured analysis."""

    def __init__(self):
        self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    def _call(self, user_message: str, max_tokens: Optional[int] = None) -> tuple[str, dict]:
        """Core call with prompt caching on the system prompt."""
        response = self._client.messages.create(
            model=settings.llm_model,
            max_tokens=max_tokens or settings.llm_max_tokens,
            system=[
                {
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},   # cache the system prompt
                }
            ],
            messages=[{"role": "user", "content": user_message}],
        )
        text = response.content[0].text
        usage = {
            "prompt_tokens": response.usage.input_tokens,
            "completion_tokens": response.usage.output_tokens,
            "cached_tokens": getattr(response.usage, "cache_read_input_tokens", 0),
        }
        return text, usage

    # ------------------------------------------------------------------
    # Public analysis methods
    # ------------------------------------------------------------------

    def analyse_failure(self, build: BuildInfo) -> AnalysisResult:
        """Full failure analysis with root cause, fix steps, and prevention."""
        prompt = FAILURE_ANALYSIS_PROMPT.format(
            job_name=build.job_name,
            build_number=build.build_number,
            result=build.result,
            duration=_duration_str(build.duration_ms),
            causes=", ".join(build.causes) or "manual/timer",
            culprits=", ".join(build.culprits) or "none recorded",
            log_length=len(build.console_log),
            console_log=build.console_log or "(no log available)",
        )
        text, usage = self._call(prompt)
        return AnalysisResult(
            job_name=build.job_name,
            build_number=build.build_number,
            result=build.result,
            analysis=text,
            **usage,
        )

    def quick_summary(self, build: BuildInfo) -> AnalysisResult:
        """Short 5-line triage summary — fast and cheap."""
        prompt = QUICK_SUMMARY_PROMPT.format(
            job_name=build.job_name,
            build_number=build.build_number,
            result=build.result,
            # Use only the last 3000 chars for quick summary
            console_log=build.console_log[-3000:] if build.console_log else "(no log)",
        )
        text, usage = self._call(prompt, max_tokens=400)
        return AnalysisResult(
            job_name=build.job_name,
            build_number=build.build_number,
            result=build.result,
            analysis=text,
            **usage,
        )

    def detect_flaky_tests(self, job_name: str, builds: list[BuildInfo]) -> str:
        """Identify flaky tests across multiple builds."""
        combined_logs = "\n\n--- Build #{} ---\n{}".join(
            f"\n\n--- Build #{b.build_number} ({b.result}) ---\n{b.console_log[-5000:]}"
            for b in builds
        )
        prompt = FLAKY_TEST_PROMPT.format(
            job_name=job_name,
            build_count=len(builds),
            combined_logs=combined_logs,
        )
        text, _ = self._call(prompt)
        return text

    def analyse_build_trend(self, job_name: str, builds: list[BuildInfo]) -> str:
        """Health assessment and trend analysis across recent builds."""
        history_lines = []
        for b in builds:
            history_lines.append(
                f"  #{b.build_number}: {b.result} ({_duration_str(b.duration_ms)})"
            )
        history = "\n".join(history_lines)
        prompt = BUILD_TREND_PROMPT.format(
            job_name=job_name,
            build_history=history,
        )
        text, _ = self._call(prompt)
        return text

    def compare_builds(self, build_a: BuildInfo, build_b: BuildInfo) -> str:
        """Side-by-side comparison of two builds."""
        prompt = COMPARE_BUILDS_PROMPT.format(
            build_a_number=build_a.build_number,
            result_a=build_a.result,
            log_a=build_a.console_log[-5000:] if build_a.console_log else "(no log)",
            build_b_number=build_b.build_number,
            result_b=build_b.result,
            log_b=build_b.console_log[-5000:] if build_b.console_log else "(no log)",
        )
        text, _ = self._call(prompt)
        return text


llm_analyzer = LLMAnalyzer()
