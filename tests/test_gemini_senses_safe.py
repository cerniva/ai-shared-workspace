import importlib.util
from pathlib import Path


def load_module():
    path = Path("scripts/gemini_senses_safe.py")
    spec = importlib.util.spec_from_file_location("gemini_senses_safe", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_reconcile_completed_duplicate_marks_only_active_copy_done():
    module = load_module()
    text = """# inbox
## TASK
id: SAME-ID
status: done
note: historical

## TASK
id: SAME-ID
status: queued
note: duplicate

## TASK
id: OTHER-ID
status: queued
note: unrelated
"""

    updated, reconciled = module.reconcile_completed_duplicates(text)

    assert reconciled == ["SAME-ID"]
    blocks = module.task_blocks(updated)
    same = [block for _, _, block in blocks if module.field(block, "id") == "SAME-ID"]
    other = [block for _, _, block in blocks if module.field(block, "id") == "OTHER-ID"]
    assert [module.field(block, "status") for block in same] == ["done", "done"]
    assert [module.field(block, "status") for block in other] == ["queued"]


def test_reconcile_without_completed_history_keeps_active_task():
    module = load_module()
    text = """## TASK
id: NEW-ID
status: queued
"""

    updated, reconciled = module.reconcile_completed_duplicates(text)

    assert updated == text
    assert reconciled == []
