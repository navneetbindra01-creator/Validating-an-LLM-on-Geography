# Validating an LLM on Geography

An experiment in automated quality validation of responses from the [Grok xAI](https://x.ai) large language model, using Geography as the subject domain.

## What This Is

Large language models can confidently give wrong answers. This project explores whether automated scoring techniques can reliably distinguish correct geography responses from incorrect ones — without a human checking each answer.

Twenty geography questions span six categories: capitals, rivers, mountains, oceans, deserts, and lakes. Each question has a ground-truth expected answer and a list of key geographic terms. After Grok responds, three independent validators score the response and a composite score determines pass or fail.

## How Validation Works

Each response is evaluated by three complementary methods:

### 1. TF-IDF Cosine Similarity (25%)
Converts the response and the expected answer into word-frequency vectors (TF-IDF) and measures the cosine of the angle between them. A score of 1.0 means identical vocabulary; 0.0 means no overlap at all. For short responses (e.g. a single place name), the score is also computed against a compact keyword string and the higher value is used — this prevents penalising a correct but brief answer against a longer expected sentence.

### 2. Semantic Similarity (50%)
Uses the `all-MiniLM-L6-v2` sentence-transformer model to encode both texts into 384-dimensional neural embeddings, then measures cosine similarity between them. Unlike TF-IDF, this captures *meaning* rather than exact vocabulary — "Canberra is the seat of government" and "The capital of Australia is Canberra" score high even though they share few words. This carries the highest weight in the composite score.

### 3. Keyword Coverage (25%)
Checks what fraction of the expected key geographic terms — place names, country names, distances, figures — appear anywhere in the response. Crucially, only *discriminating* terms are used: words that already appear in the question (e.g. "Australia" in "What is the capital of Australia?") are filtered out, so only answer-specific entities like "Canberra" count. This prevents a wrong answer from scoring well simply by mentioning the correct country or topic.

### Composite Score & Pass Threshold
```
composite = (cosine × 0.25) + (semantic × 0.50) + (keyword × 0.25)
```
A response passes when `composite ≥ 0.55`.

## Project Structure

```
├── main.py                  # Entry point (CLI)
├── runner.py                # Orchestrates parallel API calls and validation
├── grok_client.py           # Grok xAI API wrapper (OpenAI-compatible)
├── config.py                # Thresholds, weights, model settings
├── cache.py                 # Disk cache for API responses and embeddings
├── reporter.py              # Rich console table + HTML report generator
├── data_loader.py           # Loads geography Q&A dataset
├── env_loader.py            # Decrypts .env.enc at runtime
├── setup_env.py             # One-time tool: encrypts .env → .env.enc
├── data/
│   └── geography_qa.json    # 20 geography questions with expected answers
└── validators/
    ├── cosine_validator.py  # TF-IDF cosine similarity
    ├── semantic_validator.py # Sentence-transformer semantic similarity
    └── keyword_validator.py  # Key geographic term coverage
```

## Setup

**Requirements:** Python 3.11+

```powershell
pip install -r requirements.txt
```

**API key:** obtain a Grok API key from [console.x.ai](https://console.x.ai), then:

```powershell
# Create .env from the template and add your key
copy .env.example .env
# Edit .env: XAI_API_KEY=xai-your-key-here

# Encrypt it (writes .env.enc + .env.key)
py setup_env.py

# Delete the plaintext — .env.enc is used at runtime
del .env
```

> **Never commit `.env` or `.env.key`.** The `.gitignore` blocks both. Only `.env.enc` (ciphertext) is safe to commit.

## Running

```powershell
# Run all 20 questions
py main.py

# Run a specific category
py main.py --categories capitals

# Run multiple categories
py main.py --categories capitals rivers mountains

# List available categories
py main.py --list-categories

# Skip saving the HTML report
py main.py --no-save

# Clear cached responses and embeddings (forces fresh API calls)
py main.py --clear-cache
```

An HTML report is saved to `reports/report_<timestamp>.html` after each run. It shows the full Grok response alongside the expected answer for every question, keyword badges (found / missing), individual validator scores with hover tooltips, and a per-category breakdown.

## Performance

API calls run in parallel (5 workers by default). Grok responses and sentence embeddings are cached to disk, so re-runs skip the API entirely and only reload the semantic model.

| Scenario | Approximate time |
|---|---|
| First run (model download + 20 API calls) | ~30–60 s |
| Subsequent runs (model load + 20 API calls, parallel) | ~8–12 s |
| Re-run with full cache | ~2–4 s |

## Question Categories

| Category | Questions | Example |
|---|---|---|
| Capitals | 5 | What is the capital of Brazil? |
| Rivers | 3 | What is the longest river in the world? |
| Mountains | 3 | What is the highest mountain in Africa? |
| Oceans | 2 | Which ocean is the smallest in the world? |
| Countries | 3 | Which country has the most natural lakes? |
| Deserts | 2 | What is the largest hot desert in the world? |
| Lakes | 2 | What is the deepest lake in the world? |

## Findings & Observations

The experiment highlights several interesting challenges in automated LLM validation:

- **Brevity is not incorrectness.** Grok often replies with a single correct word (e.g. "Canberra") while the expected answer is a full sentence. TF-IDF alone would fail this; the keyword-fallback and semantic score compensate.
- **Topic similarity ≠ factual correctness.** A wrong answer like "Sydney is the capital of Australia" scores highly on semantic similarity because it discusses the same topic. Only keyword coverage (which checks for "Canberra" specifically) catches the error.
- **No single metric is sufficient.** Each validator has a blind spot; the composite of three independent approaches is more robust than any one alone.
