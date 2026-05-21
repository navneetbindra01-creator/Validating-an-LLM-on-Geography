"""Formats results as a rich console table and saves an HTML report."""
from __future__ import annotations

import html
from datetime import datetime
from pathlib import Path

from rich import box
from rich.console import Console
from rich.table import Table

import config
from runner import QuestionResult

console = Console(highlight=False)


def _color(passed: bool) -> str:
    return "green" if passed else "red"


# ---------------------------------------------------------------------------
# Console output
# ---------------------------------------------------------------------------

def print_summary(results: list[QuestionResult]) -> None:
    passed = sum(1 for r in results if r.passed)
    total = len(results)

    table = Table(
        title=f"Geography Validation Results  ({passed}/{total} passed)",
        box=box.ROUNDED,
        show_lines=True,
    )
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Category", style="magenta")
    table.add_column("Question", max_width=45)
    table.add_column("Cosine", justify="right")
    table.add_column("Semantic", justify="right")
    table.add_column("Keyword", justify="right")
    table.add_column("Composite", justify="right")
    table.add_column("Pass", justify="center")
    table.add_column("Error", max_width=30)

    for r in results:
        score_map = {v.name: v.score for v in r.validations}
        pass_map = {v.name: v.passed for v in r.validations}

        def fmt(name: str) -> str:
            s = score_map.get(name, 0.0)
            p = pass_map.get(name, False)
            return f"[{_color(p)}]{s:.3f}[/]"

        table.add_row(
            r.id,
            r.category,
            r.question[:45] + ("..." if len(r.question) > 45 else ""),
            fmt("cosine"),
            fmt("semantic"),
            fmt("keyword"),
            f"[bold {_color(r.passed)}]{r.composite_score:.3f}[/]",
            f"[bold {_color(r.passed)}]{'PASS' if r.passed else 'FAIL'}[/]",
            f"[red]{r.error[:30]}[/]" if r.error else "",
        )

    console.print(table)

    cats: dict[str, list[QuestionResult]] = {}
    for r in results:
        cats.setdefault(r.category, []).append(r)

    cat_table = Table(title="By Category", box=box.SIMPLE)
    cat_table.add_column("Category", style="magenta")
    cat_table.add_column("Passed", justify="center")
    cat_table.add_column("Total", justify="center")
    cat_table.add_column("Avg Score", justify="right")
    for cat, items in sorted(cats.items()):
        p = sum(1 for i in items if i.passed)
        avg = sum(i.composite_score for i in items) / len(items)
        cat_table.add_row(cat, str(p), str(len(items)), f"{avg:.3f}")

    console.print(cat_table)


# ---------------------------------------------------------------------------
# HTML report
# ---------------------------------------------------------------------------

_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
       background: #f4f6f9; color: #222; padding: 24px; }
h1 { font-size: 1.6rem; margin-bottom: 4px; }
.subtitle { color: #666; font-size: 0.9rem; margin-bottom: 24px; }

/* Summary cards */
.cards { display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 28px; }
.card { background: #fff; border-radius: 10px; padding: 20px 28px;
        box-shadow: 0 1px 4px rgba(0,0,0,.1); min-width: 140px; text-align: center; }
.card .value { font-size: 2rem; font-weight: 700; }
.card .label { font-size: 0.8rem; color: #888; margin-top: 4px; text-transform: uppercase; }
.card.pass .value { color: #16a34a; }
.card.fail .value { color: #dc2626; }

/* Category table */
.section-title { font-size: 1.1rem; font-weight: 600; margin: 24px 0 10px; }
.cat-table { width: 100%; border-collapse: collapse; background: #fff;
             border-radius: 10px; overflow: hidden;
             box-shadow: 0 1px 4px rgba(0,0,0,.08); margin-bottom: 32px; }
.cat-table th { background: #1e3a5f; color: #fff; padding: 10px 16px;
                text-align: left; font-size: 0.82rem; text-transform: uppercase; }
.cat-table td { padding: 9px 16px; border-bottom: 1px solid #eee; font-size: 0.9rem; }
.cat-table tr:last-child td { border-bottom: none; }

/* Results */
.result-card { background: #fff; border-radius: 10px; margin-bottom: 18px;
               box-shadow: 0 1px 4px rgba(0,0,0,.08); overflow: hidden; }
.result-header { display: flex; align-items: center; gap: 12px;
                 padding: 12px 18px; border-bottom: 1px solid #eee; }
.badge-id { font-family: monospace; font-size: 0.8rem; background: #e8f0fe;
            color: #1a56db; padding: 2px 8px; border-radius: 4px; }
.badge-cat { font-size: 0.78rem; background: #f0fdf4; color: #16a34a;
             padding: 2px 8px; border-radius: 4px; }
.badge-pass { margin-left: auto; font-weight: 700; font-size: 0.85rem;
              padding: 3px 12px; border-radius: 20px; }
.badge-pass.ok  { background: #dcfce7; color: #16a34a; }
.badge-pass.err { background: #fee2e2; color: #dc2626; }
.composite { font-size: 0.85rem; color: #555; }

.result-body { padding: 14px 18px; }
.qa-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 14px; }
.qa-box { background: #f8fafc; border-radius: 6px; padding: 10px 14px; }
.qa-box .qa-label { font-size: 0.72rem; text-transform: uppercase;
                    color: #888; margin-bottom: 4px; font-weight: 600; }
.qa-box .qa-text { font-size: 0.88rem; line-height: 1.5; }
.qa-box.response { border-left: 3px solid #2563eb; }
.qa-box.expected { border-left: 3px solid #16a34a; }
.error-box { background: #fff1f2; border-left: 3px solid #dc2626;
             border-radius: 6px; padding: 8px 14px; font-size: 0.83rem;
             color: #b91c1c; margin-bottom: 12px; }

/* Scores bar */
.scores { display: flex; gap: 10px; flex-wrap: wrap; }
.score-pill { display: flex; align-items: center; gap: 6px;
              background: #f1f5f9; border-radius: 20px;
              padding: 4px 12px; font-size: 0.82rem; }
.score-pill .sname { color: #555; }
.score-pill .sval  { font-weight: 700; }
.score-pill.ok  .sval { color: #16a34a; }
.score-pill.err .sval { color: #dc2626; }
.score-pill.composite { background: #1e3a5f; color: #fff; }
.score-pill.composite .sname { color: #93c5fd; }
.score-pill.composite .sval  { color: #fff; }

/* keywords */
.kw-list { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 8px; }
.kw { font-size: 0.75rem; padding: 2px 8px; border-radius: 12px; }
.kw.hit  { background: #dcfce7; color: #166534; }
.kw.miss { background: #fee2e2; color: #991b1b; text-decoration: line-through; }

/* Tooltip on score pills */
.score-pill { position: relative; cursor: help; }
.score-pill .tip {
  display: none; position: absolute; bottom: calc(100% + 6px); left: 50%;
  transform: translateX(-50%); background: #1e293b; color: #f8fafc;
  font-size: 0.75rem; line-height: 1.4; padding: 6px 10px;
  border-radius: 6px; white-space: nowrap; z-index: 10;
  box-shadow: 0 2px 8px rgba(0,0,0,.25); pointer-events: none;
  max-width: 260px; white-space: normal; text-align: left; width: max-content;
}
.score-pill:hover .tip { display: block; }

/* Methodology panel */
.method-panel { background: #fff; border-radius: 10px; margin-bottom: 28px;
                box-shadow: 0 1px 4px rgba(0,0,0,.08); overflow: hidden; }
.method-summary { padding: 12px 18px; font-weight: 600; cursor: pointer;
                  list-style: none; display: flex; align-items: center; gap: 8px;
                  font-size: 0.95rem; user-select: none; }
.method-summary::before { content: '▶'; font-size: 0.7rem; color: #888;
                           transition: transform .2s; }
details[open] .method-summary::before { transform: rotate(90deg); }
.method-body { padding: 0 18px 18px; display: grid;
               grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 14px; }
.method-card { background: #f8fafc; border-radius: 8px; padding: 12px 14px; }
.method-card h3 { font-size: 0.85rem; margin-bottom: 6px; }
.method-card p  { font-size: 0.82rem; color: #555; line-height: 1.5; }
.method-card .threshold { font-size: 0.75rem; margin-top: 6px; color: #888; }
.method-card.cosine   h3 { color: #7c3aed; }
.method-card.semantic h3 { color: #2563eb; }
.method-card.keyword  h3 { color: #0891b2; }
.method-card.composite h3 { color: #1e3a5f; }
"""

_SCORE_THRESHOLD = {"cosine": config.COSINE_THRESHOLD,
                    "semantic": config.SEMANTIC_THRESHOLD,
                    "keyword": config.KEYWORD_THRESHOLD}

_SCORE_TIPS = {
    "cosine": (
        "TF-IDF Cosine Similarity — converts both texts to word-frequency "
        "vectors and measures the angle between them. Scored against both the "
        "full expected answer and the compact keyword list; the higher of the "
        "two is used, so short correct answers (e.g. 'Canberra') are not "
        "penalised against longer expected sentences. "
        f"Pass threshold: {config.COSINE_THRESHOLD}"
    ),
    "semantic": (
        "Semantic Similarity — encodes both texts into dense neural embeddings "
        "(all-MiniLM-L6-v2) and measures how close they are in meaning, even "
        "when different words are used. Scored against both the full expected "
        "answer and the compact keyword list; the higher score wins, so short "
        "correct answers still pass. Highest weight in composite score. "
        f"Pass threshold: {config.SEMANTIC_THRESHOLD}"
    ),
    "keyword": (
        "Keyword Coverage — checks what fraction of the expected key geographic "
        "terms (place names, figures) appear anywhere in the response. "
        "A low score means important facts were omitted or named differently. "
        f"Pass threshold: {config.KEYWORD_THRESHOLD}"
    ),
    "composite": (
        f"Weighted composite: cosine x{config.WEIGHTS['cosine']:.0%} + "
        f"semantic x{config.WEIGHTS['semantic']:.0%} + "
        f"keyword x{config.WEIGHTS['keyword']:.0%}. "
        f"Standard pass threshold: {config.PASS_SCORE}. "
        f"Relaxed threshold ({config.PASS_SCORE_SHORT}) applies when the response "
        f"is fewer than 8 words and names at least one correct keyword — this "
        f"prevents penalising concise but correct answers like 'London' or 'Ben Nevis'."
    ),
}


def _score_pill(name: str, score: float) -> str:
    threshold = _SCORE_THRESHOLD.get(name, config.PASS_SCORE)
    cls = "ok" if score >= threshold else "err"
    tip = _SCORE_TIPS.get(name, "")
    return (f'<span class="score-pill {cls}">'
            f'<span class="sname">{name}</span>'
            f'<span class="sval">{score:.3f}</span>'
            f'<span class="tip">{html.escape(tip)}</span></span>')


def _keyword_badges(r: QuestionResult) -> str:
    kv = next((v for v in r.validations if v.name == "keyword"), None)
    if not kv or not r.response:
        return ""
    from data_loader import load_qa
    # pull keywords from the Q&A dataset by matching question id
    try:
        items = load_qa()
        item = next((i for i in items if i["id"] == r.id), None)
        keywords = item.get("keywords", []) if item else []
    except Exception:
        keywords = []
    if not keywords:
        return ""
    resp_lower = r.response.lower()
    badges = "".join(
        f'<span class="kw {"hit" if kw.lower() in resp_lower else "miss"}">{html.escape(kw)}</span>'
        for kw in keywords
    )
    return f'<div class="kw-list">{badges}</div>'


def _result_card(r: QuestionResult) -> str:
    status_cls = "ok" if r.passed else "err"
    status_txt = "PASS" if r.passed else "FAIL"

    score_map = {v.name: v.score for v in r.validations}
    pills = " ".join(_score_pill(n, score_map.get(n, 0.0)) for n in ("cosine", "semantic", "keyword"))
    comp_tip = html.escape(_SCORE_TIPS["composite"])
    is_short_threshold = r.pass_threshold == config.PASS_SCORE_SHORT
    threshold_label = (
        f" / threshold {r.pass_threshold} (short response)"
        if is_short_threshold
        else f" / threshold {r.pass_threshold}"
    )
    comp_pill = (f'<span class="score-pill composite">'
                 f'<span class="sname">composite</span>'
                 f'<span class="sval">{r.composite_score:.3f}'
                 f'<span style="font-weight:400;opacity:.75;font-size:.78rem">{html.escape(threshold_label)}</span>'
                 f'</span>'
                 f'<span class="tip">{comp_tip}</span></span>')

    error_html = (f'<div class="error-box">{html.escape(r.error)}</div>' if r.error else "")

    response_text = html.escape(r.response) if r.response else "<em style='color:#aaa'>No response (API error)</em>"
    expected_text = html.escape(r.expected)

    kw_badges = _keyword_badges(r)

    return f"""
<div class="result-card">
  <div class="result-header">
    <span class="badge-id">{r.id}</span>
    <span class="badge-cat">{html.escape(r.category)}</span>
    <span style="font-size:.9rem">{html.escape(r.question)}</span>
    <span class="badge-pass {status_cls}">{status_txt}</span>
  </div>
  <div class="result-body">
    {error_html}
    <div class="qa-grid">
      <div class="qa-box expected">
        <div class="qa-label">Expected answer</div>
        <div class="qa-text">{expected_text}</div>
      </div>
      <div class="qa-box response">
        <div class="qa-label">Grok response</div>
        <div class="qa-text">{response_text}</div>
      </div>
    </div>
    {kw_badges}
    <div class="scores" style="margin-top:10px">
      {pills}
      {comp_pill}
    </div>
  </div>
</div>"""


def _category_rows(results: list[QuestionResult]) -> str:
    cats: dict[str, list[QuestionResult]] = {}
    for r in results:
        cats.setdefault(r.category, []).append(r)
    rows = ""
    for cat, items in sorted(cats.items()):
        p = sum(1 for i in items if i.passed)
        avg = sum(i.composite_score for i in items) / len(items)
        color = "#16a34a" if p == len(items) else ("#ca8a04" if p > 0 else "#dc2626")
        rows += (f"<tr><td>{html.escape(cat)}</td>"
                 f"<td style='color:{color};font-weight:600'>{p}/{len(items)}</td>"
                 f"<td>{avg:.3f}</td></tr>")
    return rows


def save_html(results: list[QuestionResult], out_dir: str = config.REPORTS_DIR) -> str:
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = Path(out_dir) / f"report_{ts}.html"

    total = len(results)
    passed = sum(1 for r in results if r.passed)
    failed = total - passed
    pass_rate = passed / total * 100 if total else 0

    cards_html = "".join(_result_card(r) for r in results)
    cat_rows = _category_rows(results)
    run_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Grok Geography Validation — {run_ts}</title>
  <style>{_CSS}</style>
</head>
<body>
  <h1>Grok xAI Geography Validation</h1>
  <p class="subtitle">Model: {html.escape(config.GROK_MODEL)} &nbsp;|&nbsp; Run: {run_ts}</p>

  <div class="cards">
    <div class="card"><div class="value">{total}</div><div class="label">Total</div></div>
    <div class="card pass"><div class="value">{passed}</div><div class="label">Passed</div></div>
    <div class="card fail"><div class="value">{failed}</div><div class="label">Failed</div></div>
    <div class="card {'pass' if pass_rate >= 70 else 'fail'}">
      <div class="value">{pass_rate:.1f}%</div><div class="label">Pass Rate</div>
    </div>
  </div>

  <details class="method-panel">
    <summary class="method-summary">How Scoring Works</summary>
    <div class="method-body">
      <div class="method-card cosine">
        <h3>Cosine Similarity (TF-IDF)</h3>
        <p>Converts both the Grok response and the expected answer into word-frequency vectors using TF-IDF, then measures the cosine of the angle between them. Scored twice — once against the full expected sentence and once against the compact keyword list — and the <strong>higher score wins</strong>. This means a short but correct answer like "Canberra" is not penalised against a longer sentence like "The capital city of Australia is Canberra."</p>
        <p class="threshold">Weight: {config.WEIGHTS['cosine']:.0%} &nbsp;|&nbsp; Pass threshold: {config.COSINE_THRESHOLD}</p>
      </div>
      <div class="method-card semantic">
        <h3>Semantic Similarity</h3>
        <p>Uses the <em>all-MiniLM-L6-v2</em> neural language model to encode both texts into 384-dimensional embedding vectors, then measures cosine similarity between them. Like the cosine score, it is evaluated against both the full expected answer and the keyword list, and the <strong>higher score wins</strong>. This captures meaning rather than exact words and is the highest-weighted score in the composite.</p>
        <p class="threshold">Weight: {config.WEIGHTS['semantic']:.0%} &nbsp;|&nbsp; Pass threshold: {config.SEMANTIC_THRESHOLD}</p>
      </div>
      <div class="method-card keyword">
        <h3>Keyword Coverage</h3>
        <p>Checks what fraction of the expected key geographic terms — place names, country names, figures — appear anywhere in the Grok response. A score of 1.0 means every key term was mentioned; 0.0 means none were. Badges below each response show which terms were found (green) or missing (red, strikethrough).</p>
        <p class="threshold">Weight: {config.WEIGHTS['keyword']:.0%} &nbsp;|&nbsp; Pass threshold: {config.KEYWORD_THRESHOLD}</p>
      </div>
      <div class="method-card composite">
        <h3>Composite Score</h3>
        <p>A weighted average of the three scores above. A question is marked <strong>PASS</strong> when its composite score meets or exceeds the pass threshold. Hover over any score pill in the results below to see its description inline.</p>
        <p>When Grok replies with a very short answer (fewer than 8 words) that names at least one correct keyword, a <strong>relaxed threshold of {config.PASS_SCORE_SHORT}</strong> is applied instead of {config.PASS_SCORE}. This prevents penalising concise-but-correct answers like "London" or "Ben Nevis". Wrong short answers are unaffected because their keyword score is 0.</p>
        <p class="threshold">Standard threshold: {config.PASS_SCORE} &nbsp;|&nbsp; Short-response threshold: {config.PASS_SCORE_SHORT}</p>
      </div>
    </div>
  </details>

  <div class="section-title">Results by Category</div>
  <table class="cat-table">
    <thead><tr><th>Category</th><th>Passed</th><th>Avg Score</th></tr></thead>
    <tbody>{cat_rows}</tbody>
  </table>

  <div class="section-title">Detailed Results</div>
  {cards_html}
</body>
</html>"""

    path.write_text(html_doc, encoding="utf-8")
    return str(path)
