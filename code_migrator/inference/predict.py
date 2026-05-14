"""Inference: a Predictor protocol with three concrete backends.

Why three: a portfolio demo needs to *run* before the user has trained their
own checkpoint. So we ship:

  LocalAdapterPredictor  — loads the LoRA adapter via Unsloth + transformers.
                           Best quality once trained. Requires GPU.

  ClaudePredictor        — Anthropic Claude with a few-shot prompt that lists
                           the migration type. This is the demo path used by
                           the Next.js UI until a fine-tuned model exists.

  EchoPredictor          — Returns the input unchanged. Baseline for eval
                           comparisons; if your model can't beat echo, debug
                           training before publishing numbers.
"""
from __future__ import annotations

import os
from typing import Protocol

from ..data.schema import MigrationPair, MigrationType


class Predictor(Protocol):
    """Anything that maps a MigrationPair to a predicted modernized snippet."""

    def predict(self, pair: MigrationPair) -> str: ...


class EchoPredictor:
    def predict(self, pair: MigrationPair) -> str:
        return pair.legacy


FEW_SHOT_PROMPT = """\
You are an expert code-modernization assistant. Given a {label}, output only the
migrated code — no commentary, no explanation, no Markdown fences.

Examples:

{examples}

Now migrate this:

{input}
"""


# A tiny bank of few-shot examples per migration type. Same shape as the
# training set; in fact you can re-use the first row of train.jsonl here.
FEW_SHOT_BANK: dict[MigrationType, list[tuple[str, str]]] = {
    "jquery_to_fetch": [
        (
            "$.ajax({ url: '/api/x', success: function(d){ cb(d); } });",
            "const r = await fetch('/api/x');\nconst d = await r.json();\ncb(d);",
        ),
    ],
    "python2_to_python3": [
        ("print 'hello'", "print('hello')"),
        ("for i in xrange(n): pass", "for i in range(n): pass"),
    ],
    "callbacks_to_async_await": [
        (
            "fn(arg, function(err, res){ if (err) return cb(err); cb(null, res); });",
            "const res = await fn(arg);\ncb(null, res);",
        ),
    ],
    "class_to_hooks": [],
    "var_to_const_let": [
        ("var x = 1; var y = 2;", "const x = 1;\nconst y = 2;"),
    ],
    "commonjs_to_esm": [
        ("const a = require('a');\nmodule.exports = b;", "import a from 'a';\nexport default b;"),
    ],
}


class ClaudePredictor:
    """Uses Anthropic Claude with a few-shot prompt as a stand-in until you
    have a real fine-tuned model. Demo path for the Next.js UI."""

    def __init__(self, *, api_key: str | None = None, model: str = "claude-sonnet-4-6"):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.model = model

    def predict(self, pair: MigrationPair) -> str:
        if not self.api_key:
            raise RuntimeError("ANTHROPIC_API_KEY not set")
        import anthropic  # lazy import

        client = anthropic.Anthropic(api_key=self.api_key)
        examples = FEW_SHOT_BANK.get(pair.migration_type, [])
        examples_str = "\n\n".join(
            f"Input:\n{leg}\n\nOutput:\n{mod}" for leg, mod in examples
        ) or "(none for this migration type)"
        prompt = FEW_SHOT_PROMPT.format(
            label=_human_label(pair.migration_type),
            examples=examples_str,
            input=pair.legacy,
        )
        response = client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(b.text for b in response.content if hasattr(b, "text"))
        return _strip_code_fences(text).strip()


class LocalAdapterPredictor:
    """Loads a saved LoRA adapter and runs inference locally. GPU recommended."""

    def __init__(self, adapter_dir: str, *, max_new_tokens: int = 1024):
        self.adapter_dir = adapter_dir
        self.max_new_tokens = max_new_tokens
        self._model = None
        self._tokenizer = None

    def _load(self) -> None:
        if self._model is not None:
            return
        try:
            from unsloth import FastLanguageModel  # type: ignore
        except ImportError as e:
            raise RuntimeError(
                "Unsloth not installed; install per requirements.txt comments"
            ) from e
        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=self.adapter_dir,
            max_seq_length=2048,
            load_in_4bit=True,
        )
        FastLanguageModel.for_inference(model)
        self._model = model
        self._tokenizer = tokenizer

    def predict(self, pair: MigrationPair) -> str:
        self._load()
        tokenizer = self._tokenizer
        model = self._model
        assert tokenizer is not None and model is not None
        prompt = (
            f"<|im_start|>user\n{pair.prompt()}<|im_end|>\n<|im_start|>assistant\n"
        )
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        out = model.generate(
            **inputs,
            max_new_tokens=self.max_new_tokens,
            do_sample=False,
            temperature=0.0,
        )
        text = tokenizer.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
        return _strip_code_fences(text).strip()


def _strip_code_fences(text: str) -> str:
    """Strip leading/trailing ``` fences if the model emitted them."""
    t = text.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[1] if "\n" in t else ""
    if t.endswith("```"):
        t = t.rsplit("```", 1)[0]
    return t


def _human_label(mt: MigrationType) -> str:
    mapping = {
        "jquery_to_fetch": "jQuery AJAX call",
        "python2_to_python3": "Python 2 snippet",
        "callbacks_to_async_await": "callback-style JavaScript function",
        "class_to_hooks": "React class component",
        "var_to_const_let": "ES5 var-declaration block",
        "commonjs_to_esm": "CommonJS module",
    }
    return mapping[mt]
