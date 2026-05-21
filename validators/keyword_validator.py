import config
from .base_validator import BaseValidator, ValidationResult


class KeywordValidator(BaseValidator):
    """Measures what fraction of expected key geographic terms appear in the response."""

    @property
    def name(self) -> str:
        return "keyword"

    def validate(self, response: str, expected: str, keywords: list[str]) -> ValidationResult:
        if not keywords:
            # fall back to important words from the expected answer
            keywords = [w for w in expected.lower().split() if len(w) > 4]

        response_lower = response.lower()
        hits = [kw for kw in keywords if kw.lower() in response_lower]
        score = len(hits) / len(keywords) if keywords else 0.0

        passed = score >= config.KEYWORD_THRESHOLD
        missed = [kw for kw in keywords if kw.lower() not in response_lower]
        detail = f"Keywords found {len(hits)}/{len(keywords)}."
        if missed:
            detail += f" Missing: {', '.join(missed)}"
        return ValidationResult(
            name=self.name,
            score=round(score, 4),
            passed=passed,
            detail=detail,
        )
