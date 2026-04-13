# LogLense — LLM-Powered CI/CD Automation

LogLense connects to your Jenkins instance, fetches build logs, and uses **Claude** (via the Anthropic API) to generate structured failure summaries, root-cause analysis, flaky-test detection, and build-trend reports.

---

https://github.com/user-attachments/assets/f194feb8-7b86-4af8-b0d7-ae2a081cbd60





<img width="1438" height="856" alt="Screenshot 2026-04-13 at 2 42 33 PM" src="https://github.com/user-attachments/assets/0c6ad744-aa42-4c1b-a984-aac64a01590f" />
<img width="1440" height="900" alt="Screenshot 2026-04-13 at 2 31 07 PM" src="https://github.com/user-attachments/assets/d20e5483-cc62-4959-b51b-5de4c01a8eed" />
<img width="1440" height="900" alt="Screenshot 2026-04-13 at 2 41 44 PM" src="https://github.com/user-attachments/assets/0a94fd33-a6cb-405b-9c9e-1ba0a4998d11" />
<img width="1440" height="886" alt="Screenshot 2026-04-13 at 2 42 14 PM" src="https://github.com/user-attachments/assets/adae0307-e334-4825-bca4-922023dfa683" />


## Features

| Feature | Description |
|---|---|
| **Full Failure Analysis** | Root cause, error breakdown, fix steps, prevention tips |
| **Quick Summary** | 5-line triage — what broke & how to fix it |
| **Build Trend** | Health score + pattern analysis across recent builds |
| **Flaky Test Detection** | Identify intermittently failing tests across builds |
| **Build Comparison** | Side-by-side diff of two builds |
| **Heuristic Log Parser** | Pre-filters logs before LLM call to reduce tokens |
| **Prompt Caching** | System prompt cached to lower API costs |
| **Web Dashboard** | Dark-mode UI to browse jobs and trigger analyses |

---

## Architecture

```
loglense/
├── main.py                  # FastAPI app entry point
├── config.py                # Settings via .env
├── requirements.txt
├── jenkins/
│   └── client.py            # Async Jenkins REST API client
├── analyzer/
│   ├── llm_client.py        # Anthropic Claude integration
│   └── prompts.py           # Prompt engineering templates
├── api/
│   └── routes.py            # REST API endpoints
├── utils/
│   └── log_parser.py        # Heuristic log pre-processor
└── static/
    └── index.html           # Web dashboard
```

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and fill in:
#   JENKINS_URL, JENKINS_USER, JENKINS_TOKEN
#   ANTHROPIC_API_KEY
```

**Getting a Jenkins API token:**
1. Log in to Jenkins → click your username (top-right)
2. Configure → API Token → Add new Token

**Getting an Anthropic API key:**
Visit [console.anthropic.com](https://console.anthropic.com) → API Keys

### 3. Run the server

```bash
python main.py
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

Interactive API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/jobs` | List all Jenkins jobs |
| `GET` | `/api/v1/jobs/{job}/builds/{build}` | Get build metadata |
| `GET` | `/api/v1/jobs/{job}/builds/{build}/analyse` | Full LLM failure analysis |
| `GET` | `/api/v1/jobs/{job}/builds/{build}/quick-summary` | 5-line triage summary |
| `GET` | `/api/v1/jobs/{job}/trend` | Build trend analysis |
| `GET` | `/api/v1/jobs/{job}/flaky-tests` | Flaky test detection |
| `GET` | `/api/v1/jobs/{job}/compare?build_a=N&build_b=M` | Compare two builds |

---

## Prompt Engineering

LogLense ships five engineered prompts in `analyzer/prompts.py`:

| Prompt | Purpose |
|--------|---------|
| `FAILURE_ANALYSIS_PROMPT` | Full structured diagnosis with fix steps |
| `QUICK_SUMMARY_PROMPT` | Fast 5-line triage (low token usage) |
| `FLAKY_TEST_PROMPT` | Intermittent failure pattern detection |
| `BUILD_TREND_PROMPT` | Health scoring and stability trend |
| `COMPARE_BUILDS_PROMPT` | Regression identification between two builds |

Each prompt uses:
- **Role-setting system prompt** — positions Claude as an expert CI/CD analyst
- **Structured output sections** — forces consistent, scannable responses
- **Contextual injection** — job name, culprits, duration, and log snippets
- **Token budgeting** — logs are trimmed/condensed before injection

---

## Cost Optimization

- The system prompt is sent with `cache_control: ephemeral` — repeated calls within 5 minutes reuse the cached tokens (up to 90% cost reduction).
- The `log_parser.py` pre-processor extracts only high-signal lines before sending to the LLM, reducing input tokens by 60–80% on verbose logs.
- The Quick Summary endpoint caps output at 400 tokens for cheap triage.

---

## Example Output

```
### Failure Summary
The Maven build failed during the test phase because the database
connection pool was exhausted. All 20 allocated connections timed
out waiting for a slot...

### Root Cause
`HikariCP` connection pool limit (max=20) exceeded under parallel
test execution with `@SpringBootTest`.

### Recommended Fix
1. Add `spring.datasource.hikari.maximum-pool-size=50` to `application-test.properties`
2. Annotate integration tests with `@DirtiesContext(classMode = AFTER_EACH_TEST_METHOD)`
   to reset the application context between tests...
```
