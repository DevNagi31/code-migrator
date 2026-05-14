"""The eval harness math must hold up — BLEU calibration, parse-rate, AST sim."""
from __future__ import annotations

from code_migrator.eval.metrics import evaluate


def test_identical_strings_perfect_bleu_and_ast():
    preds = ["def f():\n    return 1"]
    refs = ["def f():\n    return 1"]
    _, summary = evaluate(preds, refs, language="python")
    # Identical → BLEU near 100, parse rate 100%, AST similarity 1.0
    assert summary.bleu_mean > 90
    assert summary.parse_rate == 1.0
    assert summary.ast_similarity_mean == 1.0


def test_totally_unrelated_strings_low_bleu():
    preds = ["def f(): return 1"]
    refs = ["class Cat: pass"]
    _, summary = evaluate(preds, refs, language="python")
    assert summary.bleu_mean < 30
    # Different program shape → AST similarity should be modest at best
    assert summary.ast_similarity_mean < 0.7


def test_parse_rate_catches_broken_python():
    preds = ["def f(\n    return 1"]  # missing close paren
    refs = ["def f():\n    return 1"]
    _, summary = evaluate(preds, refs, language="python")
    assert summary.parse_rate == 0.0


def test_parse_rate_passes_valid_js():
    """JS uses brace-balance fallback. Balanced snippet should pass."""
    preds = ["function f() { return 1; }"]
    refs = ["function f() { return 1; }"]
    _, summary = evaluate(preds, refs, language="javascript")
    assert summary.parse_rate == 1.0


def test_parse_rate_catches_unbalanced_js():
    preds = ["function f() { return 1;"]  # missing closing brace
    refs = ["function f() { return 1; }"]
    _, summary = evaluate(preds, refs, language="javascript")
    assert summary.parse_rate == 0.0


def test_renamed_python_keeps_high_ast_similarity():
    """Same program structure, different identifiers — AST sim should stay high."""
    preds = ["def foo(x):\n    return x + 1"]
    refs = ["def bar(y):\n    return y + 1"]
    _, summary = evaluate(preds, refs, language="python")
    assert summary.ast_similarity_mean > 0.8


def test_mismatched_lengths_raises():
    import pytest
    with pytest.raises(ValueError):
        evaluate(["a"], ["a", "b"])


def test_eval_summary_render_smoke():
    _, summary = evaluate(["a"], ["a"], language="python")
    rendered = summary.render()
    assert "BLEU" in rendered
    assert "Parse rate" in rendered
    assert "AST similarity" in rendered
