"""
Prompt engineering templates for CI/CD log analysis.

Each prompt is crafted to extract maximum signal from Jenkins build logs
and return structured, actionable summaries.
"""

SYSTEM_PROMPT = """You are LogLense, an expert CI/CD build analyst with deep knowledge of:
- Build tools (Maven, Gradle, npm, pip, make, Docker)
- Test frameworks (JUnit, pytest, Jest, Mocha, RSpec)
- Deployment platforms (Kubernetes, AWS, GCP, Ansible)
- Common CI/CD failure patterns and root causes

Your goal is to help developers quickly understand build failures and fix them.
Always respond in clear, structured Markdown. Be concise but complete.
Prioritize actionable insights over generic advice."""


FAILURE_ANALYSIS_PROMPT = """Analyze the following Jenkins build failure and provide a structured diagnosis.

## Build Context
- **Job**: {job_name}
- **Build #**: {build_number}
- **Result**: {result}
- **Duration**: {duration}
- **Triggered by**: {causes}
- **Culprits (recent committers)**: {culprits}

## Console Log (last {log_length} chars)
```
{console_log}
```

## Your Analysis

Provide a response in this exact structure:

### Failure Summary
One paragraph (3-5 sentences) explaining what went wrong in plain English.

### Root Cause
The most likely root cause, stated in 1-2 sentences.

### Error Breakdown
A bullet list of the specific errors/exceptions found, each with:
- The error message (quoted)
- The file/line if available
- What it means

### Affected Components
Which modules, services, or test suites failed.

### Recommended Fix
Step-by-step numbered actions the developer should take to resolve this.

### Prevention
One or two suggestions to prevent this class of failure in future builds."""


QUICK_SUMMARY_PROMPT = """You are analyzing a Jenkins build log. Give a SHORT summary (max 5 lines).

Job: {job_name} | Build: #{build_number} | Result: {result}

Log excerpt:
```
{console_log}
```

Respond with:
**Status**: [one emoji + one word]
**What failed**: [one sentence]
**Why**: [one sentence root cause]
**Fix**: [one sentence action]"""


FLAKY_TEST_PROMPT = """Analyze these Jenkins build logs and identify flaky tests.

Builds analyzed: {build_count}
Job: {job_name}

Logs:
```
{combined_logs}
```

Identify:
1. **Tests that fail intermittently** — list test names and failure rate
2. **Pattern** — timing issues, resource contention, environment setup
3. **Recommendation** — how to stabilize each flaky test"""


BUILD_TREND_PROMPT = """Analyze the build trend for Jenkins job '{job_name}'.

Recent builds:
{build_history}

Provide:
### Health Assessment
Rate the job health (Healthy / Degrading / Critical) and explain why.

### Failure Patterns
What types of failures repeat? Group by category.

### Stability Score
A score from 0-100 with breakdown.

### Top Recommendation
The single most impactful thing the team can do right now."""


COMPARE_BUILDS_PROMPT = """Compare these two Jenkins builds and explain what changed between them.

**Build A** (#{build_a_number} — {result_a}):
```
{log_a}
```

**Build B** (#{build_b_number} — {result_b}):
```
{log_b}
```

Provide:
### Key Differences
What is different in the logs?

### Regression Introduced
Did build B introduce a regression compared to A? What specifically?

### Likely Change
Based on the logs, what code or config change likely caused the difference?"""
