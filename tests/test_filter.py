"""Data filter: rejects noisy/short/wrong-license pairs."""
from __future__ import annotations

from code_migrator.data.filter import is_valid_pair
from code_migrator.data.schema import MigrationPair


def _pair(**overrides) -> MigrationPair:
    base = dict(
        migration_type="jquery_to_fetch",
        legacy="$.ajax({ url: '/api/x', success: function(d){ console.log(d); }});",
        modern="const r = await fetch('/api/x');\nconst d = await r.json();\nconsole.log(d);",
        language="javascript",
        license="MIT",
    )
    base.update(overrides)
    return MigrationPair(**base)


def test_valid_jquery_pair_passes():
    ok, reason = is_valid_pair(_pair())
    assert ok, reason


def test_legacy_too_short_rejected():
    ok, reason = is_valid_pair(_pair(legacy="$.ajax();"))
    assert not ok
    assert "length" in reason


def test_legacy_too_long_rejected():
    ok, reason = is_valid_pair(_pair(legacy="$.ajax;" + ("x" * 2000)))
    assert not ok
    assert "length" in reason


def test_wrong_license_rejected():
    ok, reason = is_valid_pair(_pair(license="GPL-3.0"))
    assert not ok
    assert "license" in reason


def test_missing_legacy_signal_rejected():
    # Legacy doesn't contain $.ajax/$.get/$.post/jQuery. — should be rejected.
    ok, reason = is_valid_pair(
        _pair(legacy="console.log('a long enough string to pass length check yeah indeed yes');")
    )
    assert not ok
    assert "signal" in reason


def test_missing_modern_signal_rejected():
    ok, reason = is_valid_pair(_pair(modern="console.log('no await, no fetch, just enough text to clear length');"))
    assert not ok
    assert "signal" in reason


def test_unbalanced_js_modern_rejected():
    ok, reason = is_valid_pair(_pair(modern="const r = await fetch('/x'); { unbalanced"))
    assert not ok
    assert "balanced" in reason or "signal" in reason or "length" in reason


def test_python_modern_parse_check():
    pair = MigrationPair(
        migration_type="python2_to_python3",
        legacy="for k, v in items.iteritems():\n    print 'k=', k, 'v=', v",
        modern="for k, v in items.items()\n    print('k=', k, 'v=', v)",  # missing colon
        language="python",
        license="MIT",
    )
    ok, reason = is_valid_pair(pair)
    assert not ok
    assert "parse" in reason
