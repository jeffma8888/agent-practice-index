#!/usr/bin/env python3
"""Banned-token scanner: keeps private material out of a public repository.

Two tiers, deliberately:

  PUBLIC_RULES   structural patterns that are safe to publish and useful to
                 anyone - absolute home paths, bare emails, IP addresses,
                 credential-shaped strings.

  private rules  literal names (an employer, a person, an internal system)
                 loaded from a gitignored JSON file if present. Literals ARE
                 the sensitive thing, so shipping them in the scanner would
                 leak precisely what the scanner exists to prevent. This is
                 not paranoia - it is the failure this repo documents twice:
                 a gate cannot see inside its own exemption (INC-0019), and a
                 clean commit identity says nothing about clean file CONTENT
                 (INC-0015). An earlier version of this file carried the
                 author's real name in a self-test sample and reported the
                 tree clean, because it skips itself.

Every rule must ship a self-test sample. `selftest()` is two-sided: each rule
must fire on its planted known-bad sample, and a known-good paragraph must not
trip any rule. A detector never proven against a known-bad sample is worthless,
and fail-open monitoring is worse than none (INC-0018).

Usage:
    python3 tools/leakscan.py [root]
    exit 0 = clean, 1 = leaks found, 2 = self-test failed (do not trust output)
"""
from __future__ import annotations
import json, os, re, sys

PRIVATE_FILE = ".leakscan-private"

# (name, regex, why, self-test sample). Matched case-insensitively.
PUBLIC_RULES: list[tuple[str, str, str, str]] = [
    ("home-path", r"/(?:Users|home)/[a-z][a-z0-9._-]*",
     "machine-local absolute path exposes an account name",
     "the log was at /Users/someone/projects/x"),
    ("bare-email", r"[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}",
     "email address in tracked content",
     "reach me at someone@example.com"),
    ("private-ip", r"\b(?:10|192\.168|172\.(?:1[6-9]|2\d|3[01]))\.\d{1,3}\.\d{1,3}\b",
     "internal network address",
     "the host was 10.0.1.42 last week"),
    ("aws-key", r"\bAKIA[0-9A-Z]{16}\b",
     "cloud access key id",
     "key AKIAIOSFODNN7EXAMPLE appeared"),
    ("bearer-token", r"\b(?:bearer|api[_-]?key|secret)\s*[:=]\s*\S{12,}",
     "credential-shaped assignment",
     "api_key = sk-abcdefghijklmnop"),
    ("private-key", r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
     "embedded private key",
     "-----BEGIN PRIVATE KEY-----"),
]

SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", ".venv", "node_modules", ".ruff_cache"}
SKIP_EXT = (".png", ".jpg", ".jpeg", ".pdf", ".bundle", ".ico", ".woff", ".woff2")
SELF = os.path.basename(__file__)

KNOWN_GOOD = (
    "The orchestrator was making progress while the reviewer kept taking the same path. "
    "A step baking for 600s is chronically over budget. Akin to a deadlock, but not one."
)


def load_private_rules(root: str) -> list[tuple[str, str, str, str]]:
    """Load literal rules from a gitignored JSON file, if the operator has one.

    Format: [{"name": "...", "pattern": "...", "why": "...", "sample": "..."}]
    Absent file is normal and not an error - a contributor has no private list.
    """
    path = os.path.join(root, PRIVATE_FILE)
    if not os.path.exists(path):
        return []
    try:
        raw = json.load(open(path, encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"WARNING: {PRIVATE_FILE} present but unreadable ({exc}); "
              f"structural rules only", file=sys.stderr)
        return []
    out = []
    for r in raw:
        try:
            out.append((r["name"], r["pattern"], r.get("why", ""), r["sample"]))
        except KeyError as exc:
            print(f"WARNING: {PRIVATE_FILE} entry missing {exc}; skipped", file=sys.stderr)
    return out


def rules_for(root: str) -> list[tuple[str, str, str, str]]:
    return PUBLIC_RULES + load_private_rules(root)


def scan_text(text: str, rules: list | None = None) -> list[tuple[str, str]]:
    hits = []
    for name, pat, _why, _sample in (rules if rules is not None else PUBLIC_RULES):
        for m in re.finditer(pat, text, re.IGNORECASE):
            hits.append((name, m.group(0)))
    return hits


def scan_repo(root: str, rules: list | None = None) -> dict[str, list[tuple[str, str]]]:
    rules = rules if rules is not None else rules_for(root)
    found: dict[str, list[tuple[str, str]]] = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            # This file holds the patterns; the private list holds the literals.
            if fn in (SELF, PRIVATE_FILE) or fn.endswith(SKIP_EXT):
                continue
            fp = os.path.join(dirpath, fn)
            try:
                text = open(fp, encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            if hits := scan_text(text, rules):
                found[os.path.relpath(fp, root)] = hits
    return found


def selftest(rules: list | None = None) -> list[str]:
    """Two-sided. Every rule fires on its planted sample; clean text stays clean."""
    rules = rules if rules is not None else PUBLIC_RULES
    failures = []
    for name, pat, _why, sample in rules:
        if not any(h[0] == name for h in scan_text(sample, rules)):
            failures.append(f"{name}: FAILED to fire on its own known-bad sample")
    if bad := scan_text(KNOWN_GOOD, rules):
        failures.append(f"false positive on known-good text: {bad}")
    return failures


def main() -> int:
    root = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))
    rules = rules_for(root)
    n_priv = len(rules) - len(PUBLIC_RULES)

    if fails := selftest(rules):
        print("SELF-TEST FAILED - scanner is not trustworthy, output means nothing:")
        for f in fails:
            print("  ", f)
        return 2
    print(f"self-test OK ({len(PUBLIC_RULES)} public + {n_priv} private rules fire "
          f"on planted samples, no false positive)")
    if not n_priv:
        print(f"note: no {PRIVATE_FILE} found - structural rules only. "
              f"See {PRIVATE_FILE}.example to add literal names before publishing.")

    if not (found := scan_repo(root, rules)):
        print(f"clean: no banned tokens under {root}")
        return 0
    print(f"LEAKS FOUND in {len(found)} file(s):")
    for fp, hits in sorted(found.items()):
        uniq = sorted({f"{n}:{v}" for n, v in hits})
        print(f"  {fp}: {', '.join(uniq[:8])}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
