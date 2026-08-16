# agent-practice-index

**A machine-readable, evidence-graded, freshness-tracked index of current industry practice for building AI agent systems — written to be read by agents at the top of a loop iteration.**

Most "best practices for AI agents" live in blog posts a human skims once. This repo turns that knowledge into a **queryable register another agent can pin into its own context, check its own project against, and keep current** — so an autonomous build loop (Ralph, a multi-role factory, agent-foundry) can improve *the way it builds* and not just *what it builds*.

It is the third of a trio, each answering a different question about agent engineering:

| Repo | Question it answers |
|---|---|
| [`agent-failure-modes`](https://github.com/jeffma8888/agent-failure-modes) | What goes *wrong*, and the transferable rule from each incident |
| [`agent-gap-radar`](https://github.com/jeffma8888/agent-gap-radar) | What is *missing / unsolved*, ranked by evidence |
| **`agent-practice-index`** (this repo) | What the industry says you *should do right now*, and whether your project does it |

## Why it is shaped this way

Three design decisions carry the whole project, each aimed at a way an "advice list" normally rots:

1. **Every claim is graded on the evidence behind it, not on how confident it sounds.** `confidence` (0–5) is *derived only* from the class of the sources cited — a vendor engineering post, a peer-reviewed paper, a first-party incident — via a closed ladder in [`taxonomy.py`](src/agent_practice_index/taxonomy.py). An LLM-generated assertion carries weight **0**: it is a hypothesis to check, never evidence for itself. A record cannot inflate its own credibility with prose.
2. **Adoption value and confidence are never blended.** `adoption_value` (how much it's worth doing) and `confidence` (how well we know it's true) are kept as separate numbers, because blending them produces the classic defect where a cheap, thinly-sourced tip outranks a well-evidenced hard one and nobody can see which input moved. Ranking sorts on value and applies confidence as a *visible filter*; below-floor records are shown, never silently dropped.
3. **Currency is the product, so staleness is computed, not assumed.** Each record carries `as_of` and a `review_days` horizon. `practice stale` reports what is past due. A practice about a fast-moving field is a *perishable claim*, and the tool says out loud when a claim hasn't been re-checked lately.

Every quote in the register is a **verbatim substring of its cited source**, verified mechanically at authoring time — not a paraphrase.

## Install

```bash
uv venv && uv pip install -e .
```

## The payoff commands

```bash
practice report .            # full ranked index (markdown), coverage + evidence base
practice list .              # one line per practice, ranked
practice show PRC-003 .      # full brief for one practice, with evidence quotes
practice digest .            # BOUNDED, agent-pinnable digest — the primary consumption path
practice stale .             # records past their re-verification horizon
practice audit --target ~/my-loop-repo .   # self-audit checklist for a project
practice prd --practice PRC-008 .          # emit a build-loop prd.json to ADOPT a practice
practice taxonomy            # the closed vocabularies + evidence ladder
```

### How an agent uses this in a loop

1. **Pin the digest.** `practice digest .` emits a character-bounded block (default 10,000 chars, 800/bullet) with every elision reported in a notice line — safe to inject into every iteration's prompt without silently blowing the step budget. This is the "read it and learn from it" path.
2. **Self-audit.** `practice audit --target <repo>` emits a checklist: each applicable practice, ranked by value, with the *one check to run* to tell whether the project already follows it. It is deliberately a checklist, not a verdict — the answer comes from the repo, not from a guess.
3. **Convert a gap into work.** `practice prd --practice <id>` emits a `prd.json` (project / branchName / userStories with `passes` flags) whose **first story is always a failing demonstration of the gap**, so a Ralph/foundry loop cannot mark a practice adopted without first observing the absence it claims to fix.
4. **Keep it current.** Any agent may add or refresh a record (see below) and open a PR. `practice validate` + `practice stale` are the gates.

## Adding or updating a practice

A record is one JSON file in [`practices/`](practices/) named `PRC-NNN-slug.json`. The schema ([`models.py`](src/agent_practice_index/models.py)) is enforced by `practice validate` and by the test suite:

- `statement` — one imperative sentence, standalone, ≤400 chars (it must survive a bounded digest).
- `check` — how to verify adoption **mechanically**, in one sentence. A practice nobody can check is an opinion, not a practice.
- `evidence` — at least one citation with a resolvable `https` locator, an ISO date, and a **verbatim** `quote`.
- `as_of` / `review_days` — when it was last verified and when to re-check.
- `applies_when` / `not_when` — scope. Absent scope is how practices get cargo-culted.
- `supersedes` / `superseded_by` — records are never deleted on becoming obsolete; they are marked `superseded` and point to the replacement.

Taxonomies (`area`, `kind`, `maturity`, evidence classes) are **closed enumerations**. A record that doesn't fit argues for a new term in a PR; it does not invent a free-text label.

Run before committing:

```bash
uv run pytest            # schema, scoring, freshness, digest bounding, CLI
practice validate .      # ids sequential, quotes present, cross-refs resolve
python3 tools/leakscan.py .          # no internal / personal identifiers (positional path)
```

## Seed register (11 records, v0.1)

Sources are public and primary: Anthropic's engineering posts on [building effective agents](https://www.anthropic.com/engineering/building-effective-agents) and [context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents), Geoffrey Huntley's [Ralph](https://ghuntley.com/ralph/) pattern, and first-party incident rules from `agent-failure-modes`. See [`INDEX.md`](INDEX.md) for the generated report and [`TAXONOMY.md`](TAXONOMY.md) for the vocabularies.

## License

MIT
