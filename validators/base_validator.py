from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ValidationResult:
    name: str
    score: float       # 0.0 – 1.0
    passed: bool
    detail: str = ""


class BaseValidator(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def validate(self, response: str, expected: str, keywords: list[str]) -> ValidationResult: ...
