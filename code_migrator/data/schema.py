"""Schema for migration training pairs.

One row per (legacy_snippet, modernized_snippet, migration_type) triple.
This is the same JSONL shape the training script expects, the eval harness
reads, and the inference API serves. Keeping it in one place means the
scraper + filter + train + eval + inference all type-check against the
same contract.
"""
from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field

MigrationType = Literal[
    "jquery_to_fetch",
    "python2_to_python3",
    "callbacks_to_async_await",
    "class_to_hooks",
    "var_to_const_let",
    "commonjs_to_esm",
]


class MigrationPair(BaseModel):
    """One training example."""

    migration_type: MigrationType
    legacy: str = Field(..., description="The source code to migrate (input).")
    modern: str = Field(..., description="The target modernized form (label).")
    language: Literal["javascript", "typescript", "python"]
    source_url: str | None = None
    license: str | None = None
    notes: str | None = None

    def prompt(self) -> str:
        """Instruction-tuning prompt format. Matches what train.py and inference use."""
        return (
            f"Migrate the following {_human_label(self.migration_type)}. "
            f"Output only the migrated code, no commentary.\n\n"
            f"```\n{self.legacy}\n```"
        )

    def target(self) -> str:
        return self.modern


def _human_label(mt: MigrationType) -> str:
    mapping = {
        "jquery_to_fetch": "jQuery AJAX call to a modern fetch + async/await",
        "python2_to_python3": "Python 2 code to Python 3",
        "callbacks_to_async_await": "callback-style JavaScript to async/await",
        "class_to_hooks": "React class component to a function component with hooks",
        "var_to_const_let": "ES5 var declarations to ES6 const/let",
        "commonjs_to_esm": "CommonJS require/module.exports to ES Modules",
    }
    return mapping[mt]
