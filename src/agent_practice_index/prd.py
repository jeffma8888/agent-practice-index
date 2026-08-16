"""Emit a build-loop prd.json for ADOPTING a practice.

This is the handoff that makes the index actionable: research becomes a story
list a Ralph-style loop or a multi-role factory can execute. The shape follows
the widely-used prd.json convention (project / branchName / userStories with a
`passes` flag), so an existing loop needs no adapter.

The first story is always "make the check fail visibly". Ordering adoption that
way means the loop cannot mark a practice adopted without having first observed
the absence it claims to have fixed - the same reason a bug fix starts with a
reproduction.
"""

from __future__ import annotations

import json
import re

from .models import Practice

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def slug(text: str, limit: int = 48) -> str:
    out = _SLUG_RE.sub("-", text.lower()).strip("-")
    return out[:limit].rstrip("-")


def build_prd(practice: Practice, project: str = "target-project") -> dict:
    stories: list[dict] = [
        {
            "id": "US-001",
            "title": f"Demonstrate the gap for {practice.id}",
            "description": (
                f"As a maintainer, I want proof this project does not yet satisfy "
                f"{practice.id} so that adoption is measured rather than asserted."
            ),
            "acceptanceCriteria": [
                f"Run the check and record the result verbatim: {practice.check}",
                "Write the observed result to the repo (not to a scratch file)",
                "If the check already passes, stop and mark this practice adopted "
                "with the evidence, instead of inventing work",
                "Tests pass",
            ],
            "priority": 1,
            "passes": False,
            "notes": f"Practice statement: {practice.statement}",
        }
    ]
    for i, step in enumerate(practice.how, start=2):
        stories.append({
            "id": f"US-{i:03d}",
            "title": step if len(step) <= 90 else step[:87] + "...",
            "description": (
                f"As a maintainer, I want to adopt {practice.id} so that: "
                f"{practice.failure_if_absent}"
            ),
            "acceptanceCriteria": [
                step,
                f"The practice check now passes: {practice.check}",
                "Tests pass",
            ],
            "priority": i,
            "passes": False,
            "notes": "",
        })
    stories.append({
        "id": f"US-{len(practice.how) + 2:03d}",
        "title": f"Lock {practice.id} in so it cannot silently regress",
        "description": (
            "As a maintainer, I want the adopted practice enforced mechanically, "
            "because a practice held only in prose decays without any signal."
        ),
        "acceptanceCriteria": [
            "Add an automated check (test, linter rule, or CI step) that fails if "
            "the practice is removed",
            "Prove it two-sided: it fails on a known-bad sample and passes on the "
            "current tree",
            "Tests pass",
        ],
        "priority": len(practice.how) + 2,
        "passes": False,
        "notes": (
            "A guardrail that has never been observed failing is not known to work."
        ),
    })

    return {
        "project": project,
        "branchName": f"practice/{practice.id.lower()}-{slug(practice.title)}",
        "description": (
            f"Adopt {practice.id}: {practice.title}. Source index: "
            f"agent-practice-index (evidence-graded, freshness-tracked)."
        ),
        "userStories": stories,
    }


def render_prd(practice: Practice, project: str = "target-project") -> str:
    return json.dumps(build_prd(practice, project), indent=2) + "\n"
