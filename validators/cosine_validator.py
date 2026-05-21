from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import config
from .base_validator import BaseValidator, ValidationResult


def _cosine(a: str, b: str) -> float:
    vectorizer = TfidfVectorizer(stop_words="english")
    try:
        tfidf = vectorizer.fit_transform([a.lower(), b.lower()])
        return float(cosine_similarity(tfidf[0], tfidf[1])[0][0])
    except ValueError:
        return 0.0


class CosineValidator(BaseValidator):
    """
    TF-IDF cosine similarity between the Grok response and the expected answer.
    Also compares against the compact keywords string and takes the higher score,
    so a short but correct answer (e.g. 'Canberra') is not penalised against a
    longer expected sentence.
    """

    @property
    def name(self) -> str:
        return "cosine"

    def validate(self, response: str, expected: str, keywords: list[str]) -> ValidationResult:
        score_full = _cosine(response, expected)

        # For short responses TF-IDF has too little vocabulary to score fairly
        # against a full sentence, so also compare against the compact keyword
        # string and take the higher score. Only do this for short responses —
        # for longer ones the full-sentence comparison is already reliable and
        # the keyword string can falsely inflate scores for wrong answers that
        # share context words like "capital" or "Australia".
        response_words = len(response.split())
        kw_string = " ".join(keywords) if keywords else ""
        if kw_string and response_words < 8:
            score_kw = _cosine(response, kw_string)
            score = max(score_full, score_kw)
            detail = f"TF-IDF cosine: {score:.4f} (vs full: {score_full:.4f}, vs keywords: {score_kw:.4f}, threshold {config.COSINE_THRESHOLD})"
        else:
            score = score_full
            detail = f"TF-IDF cosine: {score:.4f} (vs full expected, threshold {config.COSINE_THRESHOLD})"

        passed = score >= config.COSINE_THRESHOLD
        return ValidationResult(
            name=self.name,
            score=round(score, 4),
            passed=passed,
            detail=detail,
        )
