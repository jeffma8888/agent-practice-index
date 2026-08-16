# Agent practice index

Generated 2026-08-16 from 11 records. Ranked by adoption value; confidence floor 2.

| Practice | Value | Conf | Area | Kind | Maturity | Verified |
| --- | --- | --- | --- | --- | --- | --- |
| PRC-007 Success is an artifact on disk, not an exit code or a self-report | 9.5 | 5 | verification-gates | guardrail | established | 2026-08-16 |
| PRC-011 Sandbox autonomy; keep production behind a human gate | 9.5 | 3 | sandbox-safety | guardrail | established | 2026-08-16 |
| PRC-003 Treat context as a finite attention budget; spend it on the smallest high-signal set | 9.0 | 3 | context-engineering | pattern | consolidating | 2026-08-16 |
| PRC-006 One task per loop iteration, with a fresh context each time | 9.0 | 3 | loop-architecture | pattern | consolidating | 2026-08-16 |
| PRC-008 Write a minimal complete artifact first, then refine in place (checkpoint-first) | 9.0 | 5 | verification-gates | pattern | consolidating | 2026-08-16 |
| PRC-009 A verdict token that is absent must not default to the destructive answer | 9.0 | 5 | verification-gates | guardrail | consolidating | 2026-08-16 |
| PRC-010 Fast, reliable feedback loops are the precondition for useful agents | 9.0 | 5 | feedback-loops | pattern | established | 2026-08-16 |
| PRC-001 Start with the simplest thing that works; add agentic complexity only when it demonstrably helps | 8.0 | 3 | loop-architecture | pattern | established | 2026-08-16 |
| PRC-004 For long-horizon work, persist state as structured notes outside the context window | 8.0 | 3 | memory-state | pattern | consolidating | 2026-08-16 |
| PRC-002 An agent is LLMs using tools in a loop on environmental feedback - design the tools accordingly | 7.5 | 3 | tool-interface | pattern | established | 2026-08-16 |
| PRC-005 Isolate deep sub-work in sub-agents that return only a distilled summary | 7.0 | 3 | multi-agent | pattern | consolidating | 2026-08-16 |

## Statements

- **PRC-007** Decide whether a stage succeeded by checking for a concrete artifact it was required to produce, never by trusting its exit code or the agent's own claim of success.
- **PRC-011** Let agents try, fail, and retry freely inside a constrained environment, but require a human in the loop before anything reaches production; autonomy should come from the sandbox, not from trust.
- **PRC-003** Curate the context window as a finite attention budget: find the smallest set of high-signal tokens that produce the desired behavior, rather than stuffing in everything that might be relevant, because recall degrades as the window fills (context rot).
- **PRC-006** In an autonomous build loop, do exactly one task per iteration and spawn a fresh instance each time, keeping per-iteration context as small as possible, because output quality falls as the window fills.
- **PRC-008** Under any hard wall-clock cap, have each step emit a schema-valid minimal complete output within the first seconds and then improve it in place, so a kill degrades quality instead of destroying the step.
- **PRC-009** When a machine-parsed verdict decides ship-versus-revert, never let a missing token default to the destructive outcome; write the verdict early on decisive evidence and budget verification so a timeout cannot erase it.
- **PRC-010** Before expecting an agent to work autonomously on a codebase, make its feedback loop fast and reliable (quick tests, good error messages), because an agent is only as good as the signal it gets and a slow suite starves it.
- **PRC-001** Reach for the simplest design first (a single call, a fixed workflow) and add autonomous-agent complexity only when a simpler solution demonstrably falls short, because agency trades latency and cost for flexibility you may not need.
- **PRC-004** On tasks that exceed one context window, have the agent write structured notes to durable storage (a NOTES.md, a to-do list, a ledger) and read them back after a reset, so progress and decisions survive compaction.
- **PRC-002** Treat an agent as an LLM calling tools in a loop against environmental feedback, and invest in the agent-computer interface (clear tool docs, unambiguous parameters, poka-yoke arguments) as heavily as the prompt itself.
- **PRC-005** For complex research or exploration, delegate deep work to sub-agents with clean context windows and have each return only a condensed summary (roughly 1,000-2,000 tokens), so the lead agent synthesizes results without inheriting the detailed search context.

## Coverage by area

- context-engineering: 1
- cost-throughput: 0  <- no records yet
- evaluation: 0  <- no records yet
- feedback-loops: 1
- human-interface: 0  <- no records yet
- loop-architecture: 2
- memory-state: 1
- multi-agent: 1
- observability: 0  <- no records yet
- sandbox-safety: 1
- tool-interface: 1
- verification-gates: 3

## Evidence base

| Source class | Weight | Citations |
| --- | --- | --- |
| first-party-field | 5 | 0 |
| incident-postmortem | 5 | 4 |
| peer-reviewed | 4 | 0 |
| maintainer-primary | 4 | 0 |
| vendor-primary | 3 | 7 |
| practitioner-report | 3 | 2 |
| survey-aggregate | 2 | 0 |
| secondary-summary | 1 | 0 |
| model-output | 0 | 0 |
