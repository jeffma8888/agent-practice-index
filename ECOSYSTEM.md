# How the agent-engineering repos use each other

Four public repos, one data flow. Each answers a different question, and each one
consumes the previous one's output as machine-readable input rather than as a link.

```
 agent-failure-modes          agent-gap-radar            agent-practice-index           agent-foundry
 "what went WRONG"            "what is MISSING"          "what to DO now"               "the loop that BUILDS"
 incidents -> RULES.md   -->  gaps cite INC rules   -->  practices cite RULES +   -->   pins the digest each
 (## Practices section)       as evidence                tag gap:GAP-NNN                iteration; audits itself;
        |                          |                          |                         adopts via prd.json
        +------------- evidence ---+---------- evidence ------+                              |
                                                              ^                              |
                                                              +---- new incidents flow back -+
```

## The four seams, with the exact commands

### 1. failure-modes -> practice-index: incidents become candidate practices

`agent-failure-modes/RULES.md` ends with a `## Practices` section: cross-incident
rules, each a `- **[PRA-NNNN]** text` bullet plus a `_derived from:_ INC-...` line.
That format is machine-parseable, and this repo parses it:

```bash
practice from-rules ../agent-failure-modes/RULES.md .
```

It prints DRAFT records (as JSON) for every PRA practice **not yet represented here**,
detected by the `pra-nnnn` tag on existing records. The quote in each draft is the
source bullet verbatim. Drafts deliberately **fail schema validation** until their
`DRAFT-FROM-INCIDENT-RULES` markers are replaced with a real `check` and rationale,
so an unread draft cannot slip into the register.

Every completed record from this path carries tags `pra-nnnn` and `from-incident-rules`
and cites `RULES.md` as `incident-postmortem` evidence (weight 5). Example: `PRC-012`.

### 2. gap-radar <-> practice-index: which practices address which gap

Convention: a practice that mitigates a registered gap carries the tag `gap:GAP-NNN`.
Then either side can ask the question:

```bash
practice list . --tag gap:GAP-003         # practices that address gap GAP-003
practice digest . --tag gap:GAP-006       # a bounded digest scoped to one gap
```

From the gap-radar side, the gap's `build_hypothesis` is the thing to build; the
practice-index's `--tag` answer is what the industry already says about building it.
Seed links: GAP-003 <- PRC-007, PRC-008; GAP-004 <- PRC-003; GAP-005 <- PRC-004;
GAP-006 <- PRC-009, PRC-012.

Both registers cite `agent-failure-modes` rules as evidence, and both grade
confidence with the same evidence ladder (`model-output` = 0), so a reader can
compare a gap's confidence with a practice's confidence on equal terms.

### 3. practice-index -> foundry (and any Ralph-style loop): pin, audit, adopt

```bash
practice digest .                          # character-bounded block to inject per iteration
practice audit --target ../agent-foundry . # checklist: which practices does THIS repo follow?
practice prd --practice PRC-008 .          # prd.json to adopt one practice; story 1 = failing demo
```

The digest is bounded by **characters** with every elision reported in its notice
line, because an unbounded always-injected artifact is exactly the failure
`agent-failure-modes` INC-0004 records. The `prd.json` shape (project / branchName /
userStories with `passes`) is the one the Ralph loop and the foundry dispatcher
already consume, so no adapter is needed.

### 4. foundry -> failure-modes: the loop feeds the incident register

When a loop iteration fails in a new way, the write-up lands in `agent-failure-modes`
as an incident, is distilled into `RULES.md`, and (via seam 1) becomes a candidate
practice here. That closes the loop: **the builder's failures raise the bar the
builder is then audited against.**

## Shared verification, so the registers are trustworthy the same way

| Concern | Tool | Where it lives |
|---|---|---|
| Every citation still resolves | `tools/check_locators.py <records_dir>` | gap-radar (origin), practice-index (ported verbatim) |
| No personal / internal literal in tracked files | `tools/leakscan.py .` (positional path!) | failure-modes (origin), practice-index |
| Same, enforceable in CI without shipping the literals | `scripts/leak_guard.py` + base64 denylist | foundry (origin) |
| Schema = first quality gate; `model-output` weight 0 | pydantic models + closed taxonomies | gap-radar, practice-index |

`check_locators` is **not** in the test suites on purpose: the suites are offline by
contract, and a test that needs the network teaches a team to ignore red.
