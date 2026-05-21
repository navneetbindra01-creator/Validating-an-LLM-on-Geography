"""
Integration tests for the Grok xAI geography validation framework.

These tests call the real Grok API. Responses are cached after the first
run so subsequent builds complete quickly without additional API cost.

Run all tests:
    py -m pytest
"""
import pytest
import grok_client
from runner import _process_item


# ---------------------------------------------------------------------------
# Test 1 — API connectivity
# ---------------------------------------------------------------------------

def test_api_returns_response():
    """Grok API should return a non-empty string with no errors."""
    response = grok_client.ask_grok(
        "What is 2 + 2?",
        use_cache=False,  # always hit the real API for this connectivity check
    )
    assert isinstance(response, str), "Response should be a string"
    assert len(response.strip()) > 0, "Response should not be empty"


# ---------------------------------------------------------------------------
# Test 2 — One-word correct answer
# ---------------------------------------------------------------------------

def test_one_word_answer_passes():
    """
    Question:  What is the capital of England?
    Expected Grok answer: London  (one word)
    Outcome:   PASS
    """
    result = _process_item({
        "id": "test_capital_england",
        "category": "capitals",
        "question": "What is the capital of England?",
        "expected": "The capital of England is London.",
        "keywords": ["London", "England", "capital"],
    })

    assert result.error == "", (
        f"Grok API error: {result.error}"
    )
    assert result.passed, (
        f"Expected PASS but got FAIL\n"
        f"  Grok response : {result.response!r}\n"
        f"  Composite score: {result.composite_score}\n"
        f"  Validator scores: "
        + ", ".join(f"{v.name}={v.score:.3f}" for v in result.validations)
    )


# ---------------------------------------------------------------------------
# Test 3 — Two-word correct answer
# ---------------------------------------------------------------------------

def test_two_word_answer_passes():
    """
    Question:  What is the tallest mountain in the UK?
    Expected Grok answer: Ben Nevis  (two words)
    Outcome:   PASS
    """
    result = _process_item({
        "id": "test_ben_nevis",
        "category": "mountains",
        "question": "What is the tallest mountain in the UK?",
        "expected": (
            "Ben Nevis is the tallest mountain in the United Kingdom, "
            "standing at 1,345 metres above sea level in the Scottish Highlands."
        ),
        "keywords": ["Ben Nevis", "Scotland", "tallest", "1345"],
    })

    assert result.error == "", (
        f"Grok API error: {result.error}"
    )
    assert result.passed, (
        f"Expected PASS but got FAIL\n"
        f"  Grok response : {result.response!r}\n"
        f"  Composite score: {result.composite_score}\n"
        f"  Validator scores: "
        + ", ".join(f"{v.name}={v.score:.3f}" for v in result.validations)
    )
