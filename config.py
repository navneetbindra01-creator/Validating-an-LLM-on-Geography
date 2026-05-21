import os
import env_loader  # decrypts .env.enc → os.environ

env_loader.load()

XAI_API_KEY = os.getenv("XAI_API_KEY", "")
XAI_BASE_URL = "https://api.x.ai/v1"
GROK_MODEL = "grok-3-mini"

# Validation thresholds (0.0 – 1.0)
COSINE_THRESHOLD = 0.30
SEMANTIC_THRESHOLD = 0.55
KEYWORD_THRESHOLD = 0.50

# Composite scoring weights (must sum to 1.0)
WEIGHTS = {
    "cosine": 0.25,
    "semantic": 0.50,
    "keyword": 0.25,
}

PASS_SCORE = 0.55  # minimum composite score to count as "pass"

REPORTS_DIR = "reports"
