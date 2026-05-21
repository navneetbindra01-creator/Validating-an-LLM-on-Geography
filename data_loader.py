import json
from pathlib import Path

_DATA_PATH = Path("data/geography_qa.json")


def load_qa() -> list[dict]:
    return json.loads(_DATA_PATH.read_text(encoding="utf-8"))
