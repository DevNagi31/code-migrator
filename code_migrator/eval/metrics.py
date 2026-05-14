"""Evaluation metrics for code migration.

Three orthogonal signals — a single number on any one of them is misleading,
so the eval harness reports all three side-by-side.

  BLEU            — n-gram surface similarity to the reference. Cheap but
                    rewards parroting; can be high while the code is broken.
  Parse rate      — does the generated code actually parse? Anything below
                    100% means the model is emitting syntactic garbage.
  Semantic AST    — Jaccard similarity of the set of AST node types. A weak
    similarity        proxy for "did the model produce the same kind of program?"
                    — better than BLEU at distinguishing rename-only edits
                    from real structural changes.
"""
from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from typing import Sequence

import sacrebleu


@dataclass
class EvalRow:
    """Per-example eval result."""

    bleu: float            # 0-100 (sacrebleu scale)
    parses: bool
    ast_similarity: float  # 0-1


@dataclass
class EvalSummary:
    """Aggregate eval report. Print this; commit it to the model card."""

    n: int
    bleu_mean: float
    parse_rate: float
    ast_similarity_mean: float

    def render(self) -> str:
        return (
            f"Eval over {self.n} examples\n"
            f"  BLEU:           {self.bleu_mean:.2f}\n"
            f"  Parse rate:     {self.parse_rate * 100:.1f}%\n"
            f"  AST similarity: {self.ast_similarity_mean:.3f}\n"
        )


def evaluate(
    predictions: Sequence[str],
    references: Sequence[str],
    *,
    language: str = "python",
) -> tuple[list[EvalRow], EvalSummary]:
    """Compute per-example metrics + aggregate summary."""
    if len(predictions) != len(references):
        raise ValueError("predictions and references must be the same length")
    rows: list[EvalRow] = []
    for pred, ref in zip(predictions, references):
        rows.append(
            EvalRow(
                bleu=_bleu_one(pred, ref),
                parses=_parses(pred, language),
                ast_similarity=_ast_similarity(pred, ref, language),
            )
        )
    n = len(rows) or 1
    summary = EvalSummary(
        n=len(rows),
        bleu_mean=sum(r.bleu for r in rows) / n,
        parse_rate=sum(1 for r in rows if r.parses) / n,
        ast_similarity_mean=sum(r.ast_similarity for r in rows) / n,
    )
    return rows, summary


def _bleu_one(pred: str, ref: str) -> float:
    """Per-example BLEU. sacrebleu's corpus-level math, applied as N=1."""
    bleu = sacrebleu.sentence_bleu(pred, [ref])
    return float(bleu.score)


def _parses(code: str, language: str) -> bool:
    if language == "python":
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False
    # For JS/TS we don't ship a real parser. Brace-balance is a fair proxy
    # for syntactic well-formedness on the snippet sizes the model emits.
    return _balanced_js(code)


def _balanced_js(text: str) -> bool:
    stack: list[str] = []
    pairs = {")": "(", "}": "{", "]": "["}
    in_string: str | None = None
    escape = False
    for c in text:
        if escape:
            escape = False
            continue
        if in_string:
            if c == "\\":
                escape = True
            elif c == in_string:
                in_string = None
            continue
        if c in ('"', "'", "`"):
            in_string = c
        elif c in "({[":
            stack.append(c)
        elif c in ")}]":
            if not stack or stack[-1] != pairs[c]:
                return False
            stack.pop()
    return len(stack) == 0 and in_string is None


# ----------------------------- AST similarity ------------------------------

_PY_NODE_RX = re.compile(r"[A-Za-z_]+")


def _ast_similarity(pred: str, ref: str, language: str) -> float:
    """Jaccard similarity of the multiset of AST node types in pred vs ref.

    A coarse but useful structural-similarity score:
      - Identical programs → 1.0
      - Same kinds of constructs in different proportions → ~0.7-0.9
      - Different program shape → < 0.5
    """
    pred_nodes = _ast_node_counts(pred, language)
    ref_nodes = _ast_node_counts(ref, language)
    if not pred_nodes and not ref_nodes:
        return 1.0
    keys = set(pred_nodes) | set(ref_nodes)
    intersect = sum(min(pred_nodes.get(k, 0), ref_nodes.get(k, 0)) for k in keys)
    union = sum(max(pred_nodes.get(k, 0), ref_nodes.get(k, 0)) for k in keys)
    return intersect / union if union else 0.0


def _ast_node_counts(code: str, language: str) -> dict[str, int]:
    if language == "python":
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {}
        counts: dict[str, int] = {}
        for node in ast.walk(tree):
            counts[type(node).__name__] = counts.get(type(node).__name__, 0) + 1
        return counts
    # JS/TS fallback: bag of identifier-like tokens (very crude, but symmetric)
    tokens = _PY_NODE_RX.findall(code)
    counts = {}
    for tok in tokens:
        counts[tok] = counts.get(tok, 0) + 1
    return counts
