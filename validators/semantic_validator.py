from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import cache
import config
from .base_validator import BaseValidator, ValidationResult

_MODEL_NAME = "all-MiniLM-L6-v2"
_MODEL: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    global _MODEL
    if _MODEL is None:
        _MODEL = SentenceTransformer(_MODEL_NAME)
    return _MODEL


def _encode(text: str) -> np.ndarray:
    """Return embedding, using disk cache to avoid recomputing unchanged texts."""
    cached = cache.get_embedding(_MODEL_NAME, text)
    if cached is not None:
        return cached
    vector = _get_model().encode(text, convert_to_numpy=True)
    cache.set_embedding(_MODEL_NAME, text, vector)
    return vector


def _sim(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.clip(cosine_similarity([a], [b])[0][0], 0.0, 1.0))


class SemanticValidator(BaseValidator):
    """
    Semantic embedding similarity using sentence-transformers (all-MiniLM-L6-v2).
    Also compares against the compact keywords string and takes the higher score,
    so short correct answers are not penalised against longer expected sentences.
    """

    @property
    def name(self) -> str:
        return "semantic"

    def validate(self, response: str, expected: str, keywords: list[str]) -> ValidationResult:
        emb_response = _encode(response)
        emb_expected = _encode(expected)
        score_full = _sim(emb_response, emb_expected)

        # Also score against the compact keyword string
        kw_string = " ".join(keywords) if keywords else ""
        if kw_string:
            emb_kw = _encode(kw_string)
            score_kw = _sim(emb_response, emb_kw)
        else:
            score_kw = 0.0

        score = max(score_full, score_kw)
        passed = score >= config.SEMANTIC_THRESHOLD

        detail = f"Semantic cosine: {score:.4f} (vs full: {score_full:.4f}, vs keywords: {score_kw:.4f}, threshold {config.SEMANTIC_THRESHOLD})"
        return ValidationResult(
            name=self.name,
            score=round(score, 4),
            passed=passed,
            detail=detail,
        )
