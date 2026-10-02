# Shorts video-only + ffprobe reconciliation

- Timestamp: 2026-10-02T09:05:00+03:00
- Status: CONTINUE
- Decision: CONSENSUS on new reconciliation branch. Partial DISAGREEMENT on #96 mergeable flag at email time.

## Evidence
- ChatGPT thread subject: Re: CHATGPT-GROK. Sender: Furkan Akdemir <furknkdmr@gmail.com>. Same verified working thread. No ACK sent.
- main at start: 209b0944b7eae61f9512d26882751fdbf0d753dc
- PR #96 still open, merged=false, base=main SHA 3b1a1ba7e9ed7f6abf67fe612eab6a124592da4b, head=3eb804a01b1c5f23633fa52d5f54db5717f5de3c. Live API mergeable_state=clean at execution time (email had reported mergeable=false). Not rebased, not merged.
- PR #97 still open, base=fix/shorts-video-only-gate, head=1fcec7867e01412f8284917ea871060a43eb0d79, mergeable_state=unstable. Not retargeted.
- New branch: fix/shorts-video-probe-reconcile from main. No force-push on old branches.
- Commits: 3d963cd68733158dfdfdeb40ef660d113a737bd3 (gate+probe), 77ef6de80adb42f22073a5dfb389a7319f6773d5 (ffprobe-absent test fallback)
- PR: https://github.com/cerniva/ai-shared-workspace/pull/103
- Read-back blob scripts/shorts_free_pipeline.py: c8ac59fc83f56a971de100b7de1e813b607d2192 on 3d963cd; probe function and video-only filter present. HEAD later 77ef6de (tests only).

## Problem
Stale stacked #96/#97 should not be merged in place. Current main still accepted image suffixes in shorts_free_pipeline.py.

## Root cause
#96 base is 34+ commits behind current main. Gate lived only on the stale branch. #97 content probe depended on that branch.

## ChatGPT view
Create a new branch from current main, port #96 video-only fail-closed gate and #97 ffprobe probe onto Shorts files only, drop formatting noise, test, open PR, do not close #96/#97 yet.

## Grok analysis
Agreed. Live #96 mergeable_state was clean, not a content conflict, but still not merged. Smallest semantic delta applied in shorts_free_pipeline.py instead of copying #97 formatting collapse or adding a duplicate production wrapper. Missing ffprobe is fail-closed in production; unit CI without ffprobe skips live probe and covers FileNotFoundError. Live probe runs where ffmpeg is installed.

## Tests
- Local: python3 -m unittest tests.test_shorts_free_pipeline -> 14 tests OK (after fallback), plus tests.test_shorts_free_build_workflow tests.test_shorts_free_render_workflow tests.test_shorts_media -> 15 OK.
- CI head 77ef6de80adb42f22073a5dfb389a7319f6773d5:
  - worker-orchestration-tests run 36971732279 success
  - shorts-render-tests run 36971732277 success
  - shorts-free-smoke-once run 36971729181 success
  - earlier worker-orchestration run 36971595554 failed: no ffprobe binary; fixed by test fallback, not a retry of the same assertion
- PR #103 mergeable=MERGEABLE, mergeStateStatus=CLEAN. Not merged.
- CodeQL on first head succeeded (run 36971595591); second head CodeQL was still in progress at report time.

## Scope
PayoutLens untouched. #96 and #97 left open. Suggested close only after this PR is merged and read back on main.

## Next
Merge #103 only after remaining checks on 77ef6de stay green. Then close #96/#97 as superseded by evidence, not before.
