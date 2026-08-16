"""Fixed vocabularies for the practice index.

These enumerations are closed on purpose. A practice that does not fit an
existing area is a signal to argue for a new area in a pull request, not to
invent a free-text label: free text is what turns an index into a junk drawer
that no agent can filter reliably.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# WHERE the practice applies in the stack of building an agent system.
# ---------------------------------------------------------------------------
AREAS: dict[str, str] = {
    "loop-architecture": "Shape of the run: workflow vs agent, iteration boundaries, stop conditions.",
    "context-engineering": "What the model sees: steering, budgets, retrieval, compaction, notes.",
    "tool-interface": "Tool/action design: schemas, naming, error surfaces, agent-computer interface.",
    "feedback-loops": "How the agent learns it is wrong: tests, linters, graders, ground truth.",
    "verification-gates": "Deciding to accept work: verdicts, artifacts, gate placement, defaults.",
    "memory-state": "What survives an iteration: files, ledgers, handoff, retention.",
    "multi-agent": "Coordination: roles, isolation, shared resources, concurrency, back-pressure.",
    "sandbox-safety": "Blast radius: permissions, environment limits, production boundaries.",
    "observability": "Seeing inside a run: traces, distributions, attribution, health signals.",
    "cost-throughput": "Token/time/quota economics and the practices that keep a loop affordable.",
    "human-interface": "Where a person is in the loop: review, approval, escalation, trust.",
    "evaluation": "Measuring agent quality over time: evals, benchmarks, regression detection.",
}

# ---------------------------------------------------------------------------
# WHAT KIND of statement it is. This drives how an agent should apply it.
# ---------------------------------------------------------------------------
KINDS: dict[str, str] = {
    "pattern": "Do it this way by default; a positive construction.",
    "anti-pattern": "Do not do this; the named shape is known to fail.",
    "guardrail": "A mechanical constraint that makes a failure impossible, not unlikely.",
    "convention": "An arbitrary-but-agreed choice whose value is consistency.",
    "metric": "A thing to measure, and the reading that indicates trouble.",
    "process": "A sequence a team follows, not a property of the code.",
}

# ---------------------------------------------------------------------------
# How mature the practice is in the industry RIGHT NOW. This is a claim about
# consensus, not about how much we like it, and it is stated separately from
# evidence quality so the two can disagree visibly.
# ---------------------------------------------------------------------------
MATURITIES: dict[str, str] = {
    "established": "Widely recommended by independent primary sources; safe default.",
    "consolidating": "Multiple credible sources converging; expect refinement, not reversal.",
    "emerging": "Promising, thinly evidenced; adopt behind a reversible decision.",
    "contested": "Credible sources actively disagree; record BOTH sides before adopting.",
    "fading": "Was recommended, is being displaced; do not start new work on it.",
}

# ---------------------------------------------------------------------------
# Evidence credibility ladder. Index 0 is strongest.
# Load-bearing: confidence is DERIVED from this, so a record cannot inflate its
# own credibility with confident prose.
# ---------------------------------------------------------------------------
SOURCE_CLASSES: tuple[str, ...] = (
    "first-party-field",     # reproducible first-hand operation, with measurements
    "incident-postmortem",   # a specific failure that happened, with root cause
    "peer-reviewed",         # academic paper, accepted venue
    "maintainer-primary",    # docs/RFC/issue by the people who own the component
    "vendor-primary",        # vendor engineering post about their own system
    "practitioner-report",   # named practitioner writing up their own experience
    "survey-aggregate",      # survey or report across many respondents
    "secondary-summary",     # summary of someone else's primary source
    "model-output",          # produced by an LLM; NEVER sufficient on its own
)

SOURCE_WEIGHTS: dict[str, int] = {
    "first-party-field": 5,
    "incident-postmortem": 5,
    "peer-reviewed": 4,
    "maintainer-primary": 4,
    "vendor-primary": 3,
    "practitioner-report": 3,
    "survey-aggregate": 2,
    "secondary-summary": 1,
    "model-output": 0,
}

STATUSES: tuple[str, ...] = ("active", "superseded", "withdrawn")

# Default re-verification horizon. This field exists because the whole point of
# this index is currency: a practice recorded in a fast-moving field is a
# perishable claim, not a permanent truth.
DEFAULT_REVIEW_DAYS = 180
