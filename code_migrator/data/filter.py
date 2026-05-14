"""Quality filter for scraped migration pairs.

Most raw PRs scraped from GitHub are too noisy: trailing whitespace changes,
mixed concerns, lint-style sweeps. The filter rejects anything that fails
the quality bar so the training set stays small but high-signal.

Rules:
  - Both legacy and modern snippets must parse (we approximate via brace/paren
    balance for JS and `ast.parse` for Python).
  - Length must be in [40, 1200] chars (too short = trivial; too long = noisy).
  - The diff must actually contain the migration pattern (e.g., the legacy
    snippet must mention `$.ajax` for `jquery_to_fetch`).
  - License must be permissive (MIT, Apache-2.0, BSD-3-Clause, ISC, MPL-2.0).
"""
from __future__ import annotations

import ast
from .schema import MigrationPair, MigrationType

PERMISSIVE_LICENSES = {"MIT", "Apache-2.0", "BSD-3-Clause", "BSD-2-Clause", "ISC", "MPL-2.0"}

# A snippet must contain the legacy pattern to count as a meaningful migration.
LEGACY_SIGNALS: dict[MigrationType, tuple[str, ...]] = {
    "jquery_to_fetch": ("$.ajax", "$.get", "$.post", "jQuery."),
    "python2_to_python3": ("print ", "xrange", "iteritems", "u'"),
    "callbacks_to_async_await": ("function(err", "function (err", "callback("),
    "class_to_hooks": ("class ", "componentDidMount", "this.setState", "this.state"),
    "var_to_const_let": ("var ",),
    "commonjs_to_esm": ("require(", "module.exports"),
}

MODERN_SIGNALS: dict[MigrationType, tuple[str, ...]] = {
    "jquery_to_fetch": ("fetch(", "await "),
    "python2_to_python3": ("print(",),
    "callbacks_to_async_await": ("async ", "await "),
    "class_to_hooks": ("useState", "useEffect"),
    "var_to_const_let": ("const ", "let "),
    "commonjs_to_esm": ("import ", "export "),
}


def is_valid_pair(pair: MigrationPair) -> tuple[bool, str]:
    """Return (passes, reason). Reason is empty string when passes is True."""
    legacy = pair.legacy.strip()
    modern = pair.modern.strip()

    if not (40 <= len(legacy) <= 1200):
        return False, f"legacy length {len(legacy)} out of [40, 1200]"
    if not (40 <= len(modern) <= 1200):
        return False, f"modern length {len(modern)} out of [40, 1200]"

    if pair.license and pair.license not in PERMISSIVE_LICENSES:
        return False, f"non-permissive license: {pair.license}"

    # Pattern signal: legacy must contain the legacy pattern, modern must contain modern.
    legacy_signals = LEGACY_SIGNALS.get(pair.migration_type, ())
    if legacy_signals and not any(s in legacy for s in legacy_signals):
        return False, f"legacy snippet missing {pair.migration_type} signal"

    modern_signals = MODERN_SIGNALS.get(pair.migration_type, ())
    if modern_signals and not any(s in modern for s in modern_signals):
        return False, f"modern snippet missing {pair.migration_type} signal"

    # Parse check
    if pair.language == "python":
        try:
            ast.parse(modern)
        except SyntaxError as e:
            return False, f"modern Python doesn't parse: {e.msg}"
    else:
        if not _balanced(modern):
            return False, "modern snippet has unbalanced braces/parens"

    return True, ""


def _balanced(text: str) -> bool:
    """Cheap balance check for JS/TS — counts unmatched braces, parens, brackets."""
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
