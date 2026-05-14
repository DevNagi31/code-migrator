"""Schema round-trip and prompt formatting."""
from __future__ import annotations

import json
from pathlib import Path

from code_migrator.data.schema import MigrationPair


def test_load_sample_dataset_parses_every_row():
    """The shipped examples/dataset/sample.jsonl is the project's truth source.
    If any row fails to parse, the README's claims are out of sync with reality."""
    path = Path(__file__).resolve().parents[1] / "examples" / "dataset" / "sample.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    pairs = [MigrationPair.model_validate(r) for r in rows]
    assert len(pairs) >= 10
    # Every migration_type represented at least once
    types_present = {p.migration_type for p in pairs}
    assert len(types_present) >= 5


def test_prompt_includes_migration_label():
    p = MigrationPair(
        migration_type="jquery_to_fetch",
        legacy="$.ajax({ url: '/x' })",
        modern="await fetch('/x')",
        language="javascript",
    )
    assert "jQuery" in p.prompt()
    assert "fetch" in p.prompt()
    assert p.legacy in p.prompt()


def test_prompt_format_is_stable_across_migration_types():
    for mt in ["python2_to_python3", "class_to_hooks", "var_to_const_let", "commonjs_to_esm"]:
        p = MigrationPair(
            migration_type=mt,  # type: ignore[arg-type]
            legacy="x" * 50,
            modern="y" * 50,
            language="python" if mt == "python2_to_python3" else "javascript",
        )
        prompt = p.prompt()
        assert "Output only the migrated code" in prompt
        assert p.legacy in prompt
