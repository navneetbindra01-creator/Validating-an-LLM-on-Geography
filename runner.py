"""Orchestrates test runs: load Q&A, call Grok, run validators, return results."""
from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import config
import grok_client
from validators import CosineValidator, KeywordValidator, SemanticValidator
from validators.base_validator import ValidationResult

SYSTEM_PROMPT = (
    "You are a knowledgeable geography expert. "
    "Answer concisely and factually. Do not add unnecessary context."
)

# API calls are I/O-bound — threads give real parallelism here
MAX_WORKERS = 5

_VALIDATORS = [CosineValidator(), SemanticValidator(), KeywordValidator()]


@dataclass
class QuestionResult:
    id: str
    category: str
    question: str
    expected: str
    response: str
    validations: list[ValidationResult]
    composite_score: float
    passed: bool
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "category": self.category,
            "question": self.question,
            "expected": self.expected,
            "response": self.response,
            "composite_score": self.composite_score,
            "passed": self.passed,
            "error": self.error,
            "validations": [
                {"name": v.name, "score": v.score, "passed": v.passed, "detail": v.detail}
                for v in self.validations
            ],
        }


def _composite(validations: list[ValidationResult]) -> float:
    w = config.WEIGHTS
    score_map = {v.name: v.score for v in validations}
    return round(sum(w.get(name, 0) * score_map.get(name, 0.0) for name in w), 4)


def _discriminating_keywords(keywords: list[str], question: str) -> list[str]:
    """
    Filter keywords to only those NOT already present in the question text.
    Terms like 'Australia' or 'capital' repeat the question context and are not
    discriminating — only answer entities like 'Canberra' distinguish a correct
    response from a wrong one that happens to mention the right topic.
    """
    q_lower = question.lower()
    return [kw for kw in keywords if kw.lower() not in q_lower] or keywords


def _process_item(item: dict) -> QuestionResult:
    """Fetch Grok response and validate — runs concurrently per item."""
    qid = item["id"]
    question = item["question"]
    expected = item["expected"]
    keywords = item.get("keywords", [])
    # Only pass answer-entity keywords to validators, not question-context words
    discriminating_kw = _discriminating_keywords(keywords, question)

    response = ""
    validations: list[ValidationResult] = []
    error = ""
    try:
        response = grok_client.ask_grok(question, system_prompt=SYSTEM_PROMPT)
        for validator in _VALIDATORS:
            validations.append(validator.validate(response, expected, discriminating_kw))
    except Exception as exc:
        error = str(exc)

    composite = _composite(validations)

    # Short responses (< 8 words) that name at least one correct entity get a
    # relaxed pass threshold. Wrong answers hit keyword_score=0.0 so they still
    # face the full threshold even if the response happens to be short.
    score_map = {v.name: v.score for v in validations}
    if len(response.split()) < 8 and score_map.get("keyword", 0.0) > 0 and not error:
        pass_threshold = config.PASS_SCORE_SHORT
    else:
        pass_threshold = config.PASS_SCORE

    return QuestionResult(
        id=qid,
        category=item.get("category", ""),
        question=question,
        expected=expected,
        response=response,
        validations=validations,
        composite_score=composite,
        passed=composite >= pass_threshold and not error,
        error=error,
    )


def run(
    data_path: str = "data/geography_qa.json",
    categories: list[str] | None = None,
    workers: int = MAX_WORKERS,
) -> list[QuestionResult]:
    items = json.loads(Path(data_path).read_text(encoding="utf-8"))
    if categories:
        items = [i for i in items if i.get("category") in categories]

    # Preserve original order despite concurrent execution
    ordered: dict[str, QuestionResult] = {}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_process_item, item): item["id"] for item in items}
        for future in as_completed(futures):
            qid = futures[future]
            ordered[qid] = future.result()

    return [ordered[item["id"]] for item in items]
