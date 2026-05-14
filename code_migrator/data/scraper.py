"""GitHub PR scraper for migration training data.

Strategy:
  1. Search GitHub Code Search for known modernization commit-message patterns
     (e.g., "Migrate from jQuery to fetch", "Convert class to hooks").
  2. For each matching PR, pull the diff and split into (legacy, modern) pairs
     per hunk.
  3. Filter aggressively in filter.py — most PRs are too noisy to use directly.

Only the search + fetch is here. Filtering is intentionally a separate step so
you can iterate on the quality bar without re-hitting the API.

Requires GITHUB_TOKEN with read:public_repo. Free tier: 5000 req/hr.
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Iterable

from .schema import MigrationType

# Heuristic search queries per migration type. These are the strings that, in
# practice, surface high-signal migration PRs. Tweak per your scrape budget.
SEARCH_QUERIES: dict[MigrationType, list[str]] = {
    "jquery_to_fetch": [
        '"$.ajax" "fetch" in:diff language:javascript',
        '"jQuery to fetch" in:title is:pr',
    ],
    "python2_to_python3": [
        '"2to3" in:title is:pr language:python',
        '"print" "print()" "python 3" in:title is:pr',
    ],
    "callbacks_to_async_await": [
        '"async/await" "callback" in:title is:pr language:javascript',
        '"promisify" in:title is:pr language:javascript',
    ],
    "class_to_hooks": [
        '"class to hooks" in:title is:pr language:javascript',
        '"useState" "componentDidMount" in:diff language:javascript',
    ],
    "var_to_const_let": [
        '"var to const" OR "var to let" in:title is:pr',
    ],
    "commonjs_to_esm": [
        '"CommonJS to ESM" in:title is:pr',
        '"require" "import" in:title is:pr language:javascript',
    ],
}


@dataclass
class PrCandidate:
    repo: str
    number: int
    title: str
    url: str
    diff_url: str
    license: str | None
    migration_type: MigrationType


def search_candidates(
    migration_type: MigrationType,
    *,
    per_query: int = 20,
    token: str | None = None,
) -> Iterable[PrCandidate]:
    """Yield PR candidates by hitting GitHub search.

    Lazy / generator-style so callers can stop after N candidates without
    paying for the rest of the page.
    """
    from github import Github  # imported lazily so tests don't need PyGithub

    gh = Github(token or os.environ.get("GITHUB_TOKEN"))
    for query in SEARCH_QUERIES[migration_type]:
        results = gh.search_issues(query)
        for i, issue in enumerate(results):
            if i >= per_query:
                break
            try:
                pr = issue.as_pull_request()
            except Exception:
                continue
            if not pr.merged:
                continue
            yield PrCandidate(
                repo=pr.base.repo.full_name,
                number=pr.number,
                title=pr.title,
                url=pr.html_url,
                diff_url=pr.diff_url,
                license=pr.base.repo.license.spdx_id if pr.base.repo.license else None,
                migration_type=migration_type,
            )
            time.sleep(0.05)  # be polite
