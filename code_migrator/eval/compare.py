"""Compare a fine-tuned model against base and few-shot baselines.

The point of fine-tuning is to beat the cheaper options. If the trained model
doesn't outperform Qwen-base zero-shot OR base few-shot on the same eval set,
the training was wasted. This script makes that explicit.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Callable

from .metrics import EvalSummary, evaluate
from ..data.schema import MigrationPair


PredictFn = Callable[[MigrationPair], str]


def run_comparison(
    pairs: list[MigrationPair],
    predictors: dict[str, PredictFn],
) -> dict[str, EvalSummary]:
    """Run each `predictor` (label -> callable) on every pair; return summaries."""
    out: dict[str, EvalSummary] = {}
    for label, fn in predictors.items():
        preds = [fn(p) for p in pairs]
        refs = [p.modern for p in pairs]
        language = pairs[0].language if pairs else "python"
        _, summary = evaluate(preds, refs, language=language)
        out[label] = summary
    return out


def render_comparison(results: dict[str, EvalSummary]) -> str:
    """Render the side-by-side table that goes into the model card."""
    header = f"{'Model':<28} {'BLEU':>8} {'Parse':>8} {'AST sim':>10}"
    rows = [header, "─" * len(header)]
    for label, s in results.items():
        rows.append(
            f"{label:<28} {s.bleu_mean:>8.2f} {s.parse_rate*100:>7.1f}% {s.ast_similarity_mean:>10.3f}"
        )
    return "\n".join(rows)


def load_pairs(path: str) -> list[MigrationPair]:
    """Load a JSONL eval set (one MigrationPair per line)."""
    out: list[MigrationPair] = []
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        out.append(MigrationPair.model_validate(json.loads(line)))
    return out


def _cli() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--eval-set", required=True, help="JSONL of MigrationPair examples")
    args = parser.parse_args()
    pairs = load_pairs(args.eval_set)
    print(f"Loaded {len(pairs)} eval examples")
    # Without a trained model, just run the trivial "echo the input" predictor
    # as a sanity check baseline. Real comparison happens in train_and_eval.py.
    results = run_comparison(pairs, {"echo (baseline)": lambda p: p.legacy})
    print(render_comparison(results))


if __name__ == "__main__":
    _cli()
