"""
Entry point for the Grok xAI geography validation framework.

Usage:
    python main.py                                        # run all questions
    python main.py --categories capitals                  # run one category
    python main.py --categories capitals rivers mountains
    python main.py --no-save                              # skip HTML report
    python main.py --list-categories                      # show available categories
    python main.py --clear-cache                          # wipe cached responses/embeddings
"""
import argparse
import json
import sys
from pathlib import Path

from rich.console import Console

import cache
import reporter
import runner

console = Console(highlight=False)

DATA_PATH = "data/geography_qa.json"


def list_categories() -> None:
    items = json.loads(Path(DATA_PATH).read_text(encoding="utf-8"))
    cats = sorted({i.get("category", "unknown") for i in items})
    console.print("[bold]Available categories:[/]", ", ".join(cats))


def main() -> None:
    parser = argparse.ArgumentParser(description="Grok xAI Geography Validation Framework")
    parser.add_argument("--categories", nargs="+", metavar="CAT", help="Filter by category")
    parser.add_argument("--no-save", action="store_true", help="Do not write HTML report")
    parser.add_argument("--list-categories", action="store_true", help="List categories and exit")
    parser.add_argument("--clear-cache", action="store_true", help="Wipe response and embedding cache then exit")
    args = parser.parse_args()

    if args.clear_cache:
        cache.clear()
        return

    if args.list_categories:
        list_categories()
        return

    console.rule("[bold cyan]Grok xAI Geography Validation[/]")

    if args.categories:
        console.print(f"[dim]Filtering categories: {', '.join(args.categories)}[/]")

    console.print("[dim]Loading semantic model (first run downloads ~80 MB)...[/]")
    results = runner.run(data_path=DATA_PATH, categories=args.categories)

    reporter.print_summary(results)

    if not args.no_save:
        path = reporter.save_html(results)
        console.print(f"\n[dim]HTML report saved -> {path}[/]")

    failed = [r for r in results if not r.passed]
    if failed:
        console.print(f"\n[bold red]{len(failed)} question(s) failed.[/]")
        sys.exit(1)
    else:
        console.print("\n[bold green]All questions passed.[/]")


if __name__ == "__main__":
    main()
