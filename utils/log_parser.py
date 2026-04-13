"""
Heuristic log parser — extracts structured failure signals from raw console output
before sending to the LLM, so the LLM gets a cleaner, denser context.
"""

import re
from dataclasses import dataclass, field


# Regex patterns for common failure signals
_PATTERNS = {
    "java_exception":    re.compile(r"((?:\w+\.)+\w+Exception[^\n]*)", re.MULTILINE),
    "python_traceback":  re.compile(r"(Traceback \(most recent call last\)[\s\S]+?(?=\n\S|\Z))", re.MULTILINE),
    "npm_error":         re.compile(r"(npm ERR![^\n]+)", re.MULTILINE),
    "gradle_error":      re.compile(r"(FAILURE: Build failed[^\n]*(?:\n> [^\n]+)*)", re.MULTILINE),
    "maven_error":       re.compile(r"(\[ERROR\][^\n]+)", re.MULTILINE),
    "docker_error":      re.compile(r"(Error response from daemon:[^\n]+)", re.MULTILINE),
    "test_failure":      re.compile(r"(FAILED|FAILURE|AssertionError|test.*FAILED)[^\n]*", re.MULTILINE | re.IGNORECASE),
    "oom_error":         re.compile(r"(OutOfMemoryError|Cannot allocate memory|Killed)[^\n]*", re.MULTILINE),
    "exit_code":         re.compile(r"(Process exited with code [1-9]\d*|exit code: [1-9]\d*)", re.MULTILINE | re.IGNORECASE),
    "connection_error":  re.compile(r"(Connection refused|ECONNREFUSED|timeout|timed out)[^\n]*", re.MULTILINE | re.IGNORECASE),
}

# Lines containing these tokens are "error lines"
_ERROR_KEYWORDS = re.compile(
    r"\b(error|exception|fatal|failed|failure|cannot|could not|no such file|permission denied|not found)\b",
    re.IGNORECASE,
)

# Lines to skip (noise)
_SKIP_PATTERNS = re.compile(
    r"(Downloading|Downloaded|Progress|^\s*\[INFO\] ---|\[INFO\] Building|\[INFO\] BUILD SUCCESS)",
    re.IGNORECASE,
)


@dataclass
class ParsedLog:
    raw_length: int
    error_lines: list[str] = field(default_factory=list)
    matched_patterns: dict[str, list[str]] = field(default_factory=dict)
    failed_tests: list[str] = field(default_factory=list)
    condensed: str = ""     # high-signal excerpt to pass to LLM


def parse_console_log(log: str) -> ParsedLog:
    """
    Extract failure signals from a raw Jenkins console log.
    Returns a ParsedLog with:
      - error_lines: lines that look like errors
      - matched_patterns: named error categories and their occurrences
      - failed_tests: test names that explicitly failed
      - condensed: a shorter, signal-dense version of the log
    """
    result = ParsedLog(raw_length=len(log))

    lines = log.splitlines()

    # --- 1. Extract error lines ---
    for line in lines:
        if _SKIP_PATTERNS.search(line):
            continue
        if _ERROR_KEYWORDS.search(line):
            result.error_lines.append(line.strip())

    # --- 2. Named pattern matching ---
    for name, pattern in _PATTERNS.items():
        matches = pattern.findall(log)
        if matches:
            # Deduplicate while preserving order
            seen = set()
            unique = []
            for m in matches:
                text = m.strip()
                if text not in seen:
                    seen.add(text)
                    unique.append(text)
            result.matched_patterns[name] = unique[:10]   # cap at 10 per category

    # --- 3. Detect failed test names ---
    test_failure_re = re.compile(
        r"(?:FAILED|FAILURE|✗|✘)\s+([\w./: -]+(?:Test|Spec|Suite|test|spec)[^\s]*)",
        re.IGNORECASE,
    )
    for m in test_failure_re.finditer(log):
        name = m.group(1).strip()
        if name not in result.failed_tests:
            result.failed_tests.append(name)

    # --- 4. Build a condensed view ---
    result.condensed = _build_condensed(lines, result)

    return result


def _build_condensed(lines: list[str], parsed: ParsedLog) -> str:
    """
    Build a condensed log string: last 50 lines + all error lines,
    deduped and joined. Target: ~4 000 chars.
    """
    tail = lines[-50:]

    condensed_parts = []

    if parsed.matched_patterns:
        condensed_parts.append("=== DETECTED FAILURE PATTERNS ===")
        for category, items in parsed.matched_patterns.items():
            condensed_parts.append(f"[{category.upper()}]")
            condensed_parts.extend(f"  {item}" for item in items[:3])

    if parsed.failed_tests:
        condensed_parts.append("\n=== FAILED TESTS ===")
        condensed_parts.extend(f"  - {t}" for t in parsed.failed_tests[:20])

    condensed_parts.append("\n=== BUILD TAIL (last 50 lines) ===")
    condensed_parts.extend(tail)

    condensed = "\n".join(condensed_parts)

    # Trim to 8 000 chars if still too big
    if len(condensed) > 8_000:
        condensed = condensed[-8_000:]

    return condensed
