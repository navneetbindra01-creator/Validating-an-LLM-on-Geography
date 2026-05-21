import config
from .base_validator import BaseValidator, ValidationResult

# Short responses don't have room to mention all key terms, so we lower the
# bar to "at least 1 keyword found" rather than requiring 50% coverage.
_SHORT_RESPONSE_WORDS = 8


class KeywordValidator(BaseValidator):
    """Measures what fraction of expected key geographic terms appear in the response."""

    @property
    def name(self) -> str:
        return "keyword"

    def validate(self, response: str, expected: str, keywords: list[str]) -> ValidationResult:
        if not keywords:
            keywords = [w for w in expected.lower().split() if len(w) > 4]

        response_lower = response.lower()
        hits = [kw for kw in keywords if kw.lower() in response_lower]
        score = len(hits) / len(keywords) if keywords else 0.0

        # For short responses, require only 1 keyword hit rather than the full
        # threshold — "Amazon River" correctly hitting "Amazon" should pass even
        # if "South America" and "freshwater" are missing from a 2-word reply.
        if len(response.split()) < _SHORT_RESPONSE_WORDS and keywords:
            effective_threshold = min(config.KEYWORD_THRESHOLD, 1.0 / len(keywords))
        else:
            effective_threshold = config.KEYWORD_THRESHOLD

        passed = score >= effective_threshold
        missed = [kw for kw in keywords if kw.lower() not in response_lower]
        detail = f"Keywords found {len(hits)}/{len(keywords)} (threshold {effective_threshold:.2f})."
        if missed:
            detail += f" Missing: {', '.join(missed)}"
        return ValidationResult(
            name=self.name,
            score=round(score, 4),
            passed=passed,
            detail=detail,
        )
