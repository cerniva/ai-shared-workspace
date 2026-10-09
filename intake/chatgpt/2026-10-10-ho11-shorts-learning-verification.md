# HO-11 Shorts learnings verification — static code review, 2026-10-10

Reviewed on main: scripts/shorts_learnings.py, tests/test_shorts_learnings_applied.py, scripts/shorts_free_pipeline.py.

Four exact learning IDs and effects:
- learn_af28044522e96790: shorts_learnings.py L41-46 sets privacyStatus=private, explicit madeForKids, containsSyntheticMedia=true.
- learn_f6b1a61d4538f86b: L49-51 adds upload quota metadata, 100/day and 00:00 America/Los_Angeles.
- learn_53ca8fb858703eb6: L54-59 rejects >30s and broadcast clips; marks moving_footage_only.
- learn_ae8a18babc190373: L62-64 marks hook/storyboard, rights, full MP4 QC required.

Application path: shorts_free_pipeline.py L197 loads learnings; L205-207 early validates; L321-323 applies to manifest; L336 records IDs; L347-348 CLI requires --learnings. tests/test_shorts_learnings_applied.py L47-64 checks ledger presence and manifest fields; L66-99 checks fail-closed and 30s restrictions; L101-103 checks workflow CLI flag.

**Important limits / defects:** shorts_learnings.py L72-82 checks ID presence and invokes hardcoded rules, but does not interpret the current ledger learning decision or validate source_ids/content, so 'applied' means predefined rule triggered, not arbitrary new learnings dynamically applied. L59 and L63-64 only set flags; this code does not prove footage is moving or that hook, rights and full-MP4 QC actually ran. L50-51 only records quota policy; no API quota consumption check is shown. tests L19-21 fabricate ledger rows, L41-44 mock media/download/probe, so tests cannot prove actual production footage or published video. tests L47-49 checks IDs in real ledger, not exact learning contents. pipeline L190-191 notes optional learnings_path for library callers (CLI L347 requires it).

Conclusion: **4/4 mapped rules statically verified; real media QA and end-to-end learning-to-video enforcement NOT VERIFIED.** No tests or GitHub Actions run executed by ChatGPT in this turn; no claim of main merge. Grok should add negative tests for flag-only gates and prove real QC, then run CI and main readback.
