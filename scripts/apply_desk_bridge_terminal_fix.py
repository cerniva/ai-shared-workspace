#!/usr/bin/env python3
from pathlib import Path

path = Path("scripts/desk_bridge.py")
text = path.read_text(encoding="utf-8")

old_terminal = '''    if mid in replies or msg_status == "superseded":
        return "answered"
    if existing.get("status") == "answered":
'''
new_terminal = '''    if mid in replies or msg_status == "superseded":
        return "answered"
    # A terminal source message must clear a stale pending/seen/delayed
    # delivery state. Team reports are different: they are broadcast records
    # and still require a reader acknowledgement even when status=done.
    if channel != "team-reports" and msg_status in {"done", "blocked"}:
        return "answered"
    if existing.get("status") == "answered":
'''
if old_terminal not in text:
    raise SystemExit("terminal-status patch target not found")
text = text.replace(old_terminal, new_terminal, 1)

old_retry = '"retry": "workflow job fails closed; next schedule (*/15) or workflow_dispatch reruns reconcile. Unsaved transitions stay absent and are retried. Emitted event keys are not repeated.",'
new_retry = '"retry": "workflow job fails closed; next hourly schedule (0 * * * *) or workflow_dispatch reruns reconcile. Unsaved transitions stay absent and are retried. Emitted event keys are not repeated.",'
if old_retry not in text:
    raise SystemExit("retry metadata patch target not found")
text = text.replace(old_retry, new_retry, 1)

old_schedule = '"schedule": "*/15 * * * *",'
new_schedule = '"schedule": "0 * * * *",'
if old_schedule not in text:
    raise SystemExit("schedule metadata patch target not found")
text = text.replace(old_schedule, new_schedule, 1)

path.write_text(text, encoding="utf-8")
