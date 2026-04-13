<div align="center">

<img src="https://img.shields.io/badge/powered%20by-Claude%20AI-blueviolet?style=for-the-badge&logo=anthropic" alt="Powered by Claude"/>
<img src="https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi" alt="FastAPI"/>
<img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python" alt="Python"/>
<img src="https://img.shields.io/badge/Jenkins-CI/CD-D24939?style=for-the-badge&logo=jenkins" alt="Jenkins"/>

# 🔍 LogLense

### *Stop reading build logs. Start understanding them.*

LogLense connects to your Jenkins instance, pulls build logs, and uses **Claude AI** to instantly diagnose failures, spot flaky tests, and surface build trends — so your team spends time fixing problems, not hunting for them.

[Features](#-features) · [Architecture](#-architecture) · [Quick Start](#-quick-start) · [API Reference](#-api-reference) · [Prompt Engineering](#-prompt-engineering) · [Cost Optimization](#-cost-optimization)

---

</div>

## 🎯 The Problem

When a CI build fails, you open a 3,000-line log file, grep for "ERROR", read stack traces, chase dependency errors, and 20 minutes later you *might* know what happened. Multiply that by every developer on your team, every broken build, every day.

**LogLense turns that 20-minute debugging session into a 5-second answer.**

---

## ✨ Features

| Feature | What it does |
|---------|-------------|
<img width="1440" height="900" alt="Screenshot 2026-04-13 at 2 31 07 PM" src="https://github.com/user-attachments/assets/3567b763-5e15-445f-aa92-067820daeab7" />
| **Full Failure Analysis** | Root cause, error breakdown, step-by-step fix instructions, and prevention tips |
| **Quick Summary** | A 5-line triage — what broke and exactly how to fix it |
| **Build Trend Report** | Health score + stability pattern across your recent build history |
| **Flaky Test Detection** | Identifies tests that pass sometimes and fail others — across builds |
| **Build Comparison** | Side-by-side diff between any two builds to pinpoint regressions |
| **Heuristic Log Parser** | Pre-filters verbose logs before the LLM sees them, cutting tokens by 60–80% |
| **Prompt Caching** | System prompts cached with Anthropic's API — up to 90% cost reduction on repeated calls |
| **Web Dashboard** | Dark-mode UI to browse jobs, trigger analyses, and review results |


---


## 🧠 How It Works

```
┌─────────────────┐     REST API      ┌──────────────────┐
│                 │ ───────────────►  │                  │
│  Jenkins Server │                   │   LogLense API   │
│                 │ ◄───────────────  │   (FastAPI)      │
└─────────────────┘    Build Logs     └────────┬─────────┘
                                               │
                                    ┌──────────▼──────────┐
                                    │   Log Pre-Processor  │
                                    │  (60–80% token cut)  │
                                    └──────────┬──────────┘
                                               │
                                    ┌──────────▼──────────┐
                                    │   Claude AI (API)    │
                                    │  Engineered Prompts  │
                                    │  + Prompt Caching    │
                                    └──────────┬──────────┘
                                               │
                                    ┌──────────▼──────────┐
                                    │  Structured Output   │
                                    │  Root Cause · Fixes  │
                                    │  Trends · Flakiness  │
                                    └─────────────────────┘
```

1. **Fetch** — LogLense calls the Jenkins REST API to pull build metadata and raw console logs.
2. **Pre-process** — A heuristic parser scans the log and extracts only high-signal lines (errors, warnings, stack traces), drastically reducing tokens sent to the LLM.
3. **Analyze** — The filtered log is injected into a carefully engineered prompt and sent to Claude via the Anthropic API.
4. **Return** — Claude responds with structured, actionable output: root cause, recommended fix, and prevention advice.

---

## 🗂 Architecture

```
loglense/
├── main.py                  # FastAPI app entry point
├── config.py                # Settings loaded from .env
├── requirements.txt
│
├── jenkins/
│   └── client.py            # Async Jenkins REST API client
│
├── analyzer/
│   ├── llm_client.py        # Anthropic Claude integration + caching
│   └── prompts.py           # Five engineered prompt templates
│
├── api/
│   └── routes.py            # REST API endpoint definitions
│
├── utils/
│   └── log_parser.py        # Heuristic log pre-processor
│
└── static/
    └── index.html           # Web dashboard (dark mode)
```

The project is intentionally lean. There's no database — everything is fetched live from Jenkins and processed in-request. The only state is Anthropic's prompt cache, which lives on their infrastructure.

---

## 🚀 Quick Start

### 1. Install dependencies

```bash
git clone https://github.com/your-org/loglense.git
cd loglense
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Open `.env` and fill in your credentials:

```env
JENKINS_URL=https://jenkins.your-company.com
JENKINS_USER=your-username
JENKINS_TOKEN=your-api-token

ANTHROPIC_API_KEY=sk-ant-...
```

<details>
<summary><b>🔑 How to get a Jenkins API token</b></summary>

1. Log in to Jenkins
2. Click your username in the top-right corner
3. Go to **Configure** → **API Token**
4. Click **Add new Token**, give it a name, and copy the value

</details>

<details>
<summary><b>🔑 How to get an Anthropic API key</b></summary>

Visit [console.anthropic.com](https://console.anthropic.com) → **API Keys** → **Create Key**

</details>

### 3. Start the server

```bash
python main.py
```

| Interface | URL |
|-----------|-----|
| Web Dashboard | http://localhost:8000 |
| Interactive API Docs | http://localhost:8000/docs |

---

## 📡 API Reference

All endpoints are read-only GET requests — LogLense never writes to Jenkins.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/jobs` | List all Jenkins jobs |
| `GET` | `/api/v1/jobs/{job}/builds/{build}` | Get build metadata |
| `GET` | `/api/v1/jobs/{job}/builds/{build}/analyse` | **Full AI failure analysis** |
| `GET` | `/api/v1/jobs/{job}/builds/{build}/quick-summary` | **5-line triage summary** |
| `GET` | `/api/v1/jobs/{job}/trend` | Build trend & health score |
| `GET` | `/api/v1/jobs/{job}/flaky-tests` | Flaky test detection |
| `GET` | `/api/v1/jobs/{job}/compare?build_a=N&build_b=M` | Compare two builds |

### Example response

https://github.com/user-attachments/assets/435ba882-11c0-4f43-a526-f555e51c57fe

<img width="1440" height="886" alt="Screenshot 2026-04-13 at 2 42 14 PM" src="https://github.com/user-attachments/assets/8f7ba45b-2d83-49e4-a556-4636a25523a8" />

<img width="1440" height="900" alt="Screenshot 2026-04-13 at 2 41 44 PM" src="https://github.com/user-attachments/assets/82602369-0bc6-4344-bee2-23ef3ba99482" />

---

## 🧩 Prompt Engineering

LogLense ships five production-grade prompts in `analyzer/prompts.py`, each tuned for a specific analysis task:

| Prompt | Purpose | Token budget |
|--------|---------|-------------|
| `FAILURE_ANALYSIS_PROMPT` | Full structured diagnosis with fix steps | ~800 tokens out |
| `QUICK_SUMMARY_PROMPT` | Fast 5-line triage | 400 tokens out |
| `FLAKY_TEST_PROMPT` | Intermittent failure pattern detection | ~600 tokens out |
| `BUILD_TREND_PROMPT` | Health scoring and stability analysis | ~700 tokens out |
| `COMPARE_BUILDS_PROMPT` | Regression identification between two builds | ~800 tokens out |

Every prompt follows the same design principles:

- **Role framing** — Claude is positioned as a senior CI/CD reliability engineer with deep knowledge of the specific build system (Maven, Gradle, npm, etc.)
- **Structured output sections** — Responses always follow a consistent schema (`### Failure Summary`, `### Root Cause`, etc.), making them easy to parse and display
- **Contextual injection** — Job name, build number, triggering culprits, duration, and exit code are injected alongside the log snippet
- **Token budgeting** — `max_tokens` is capped per prompt type; logs are trimmed to fit the context window before injection

---

## 💰 Cost Optimization

LogLense is built to stay cheap at scale.

**Prompt Caching** — The system prompt is flagged with `cache_control: ephemeral`. Anthropic caches it server-side for 5 minutes. Repeated analyses of different builds within that window skip re-tokenizing the system prompt entirely — up to **90% cost reduction** on the cached portion.

**Heuristic Pre-processing** — `log_parser.py` scans each log before it reaches the LLM. It extracts error lines, stack traces, warnings, and test failure output, discarding the boilerplate. Typical verbose Maven or Gradle logs shrink by **60–80%** before the API call.

**Output Caps** — The Quick Summary endpoint is hard-capped at 400 output tokens. If you only need triage, you don't pay for a full analysis.

---

## 🛠 Tech Stack

- **[FastAPI](https://fastapi.tiangolo.com/)** — Async Python web framework with built-in OpenAPI docs
- **[Anthropic Python SDK](https://github.com/anthropic/anthropic-sdk-python)** — Claude API client with prompt caching support
- **[httpx](https://www.python-httpx.org/)** — Async HTTP client for Jenkins API calls
- **Vanilla HTML/CSS/JS** — Lightweight dark-mode dashboard, no frontend build step required

---

## 📄 License

MIT — see [LICENSE](LICENSE) for details.

---

<div align="center">

Built with ☕ and [Claude](https://anthropic.com) · Issues welcome · PRs welcome

</div>
