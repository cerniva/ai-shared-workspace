# Archive integrity evidence — 2026-10-10 22:30 TRT

Scope: read-only verification and proposed fix; no protected file changed.

- `messages/grok-to-chatgpt.md` blob SHA `5064d6885218743db420c769bbb0c578b18a5283`: isolated `dummy` at line 5026.
- `scripts/archive_heal.py` blob SHA `93a298ac091017d9388751c7fad6af5cd7c96359`: `BODY_SENTINEL` does not recognize the isolated `dummy` line.
- `state/handoffs.json` blob SHA `2c7e05ea8b6a001d97b67ce1aa91ada9c3a83b3b`: JSON parses, 15 records; HO-20261009-03 claimed, HO-20261009-08 open, HO-IMP-20261010-slow-github-actions-in-update-1620214326 open, HO-20261010-13 done.
- PR #131 head `3fa345571ec7dc4e3f28070e8e6414b764894d69`: workflow run 38017936776 failed; head vs main diverged (main ahead 358, head ahead 6).
- Proposal: add exact standalone `dummy` to sentinel guard, regression test, compare old/new message IDs, and clean only proven foreign line on a separate authorized branch. Do not rewrite protected archives without read-back and blob SHA lease.
- Blocker: attempted `scripts/archive_heal.py` update rejected by connector safety check. No code commit or CI test.
