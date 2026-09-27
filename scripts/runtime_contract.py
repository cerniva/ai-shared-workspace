from __future__ import annotations

from collections.abc import Mapping
from typing import Any

CONTRACT_VERSION = 1
ALLOWED_ACTION_CLASSES = frozenset({"read", "prepare"})
ALLOWED_CONNECTOR_OPERATIONS = frozenset({("synthetic", "echo")})
REQUIRED_FIELDS = (
    "id",
    "generation",
    "task_type",
    "connector",
    "operation",
    "action_class",
    "params",
    "created_at",
)


def idempotency_key(item: Mapping[str, Any]) -> str:
    return f"{item['id']}:{item['generation']}"


def validate_dispatch_item(item: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in REQUIRED_FIELDS:
        if field not in item:
            errors.append(f"missing required field: {field}")

    if errors:
        return errors

    if not isinstance(item.get("id"), str) or not item["id"].strip():
        errors.append("id must be a non-empty string")
    if not isinstance(item.get("generation"), int) or item["generation"] < 1:
        errors.append("generation must be an integer >= 1")
    if not isinstance(item.get("task_type"), str) or not item["task_type"].strip():
        errors.append("task_type must be a non-empty string")
    if not isinstance(item.get("params"), Mapping):
        errors.append("params must be an object")
    if not isinstance(item.get("created_at"), str) or not item["created_at"].strip():
        errors.append("created_at must be a non-empty string")

    action_class = item.get("action_class")
    if action_class not in ALLOWED_ACTION_CLASSES:
        errors.append(f"unsupported action_class for v1: {action_class}")

    pair = (item.get("connector"), item.get("operation"))
    if pair not in ALLOWED_CONNECTOR_OPERATIONS:
        errors.append(f"connector/operation not allowlisted: {pair[0]}:{pair[1]}")

    return errors


def validate_dispatch_document(data: Any) -> list[str]:
    if not isinstance(data, Mapping):
        return ["dispatch document must be an object"]
    if data.get("version") != CONTRACT_VERSION:
        return [f"unsupported dispatch version: {data.get('version')}"]
    items = data.get("items")
    if not isinstance(items, list):
        return ["items must be a list"]

    errors: list[str] = []
    for index, item in enumerate(items):
        if not isinstance(item, Mapping):
            errors.append(f"items[{index}] must be an object")
            continue
        for error in validate_dispatch_item(item):
            errors.append(f"items[{index}]: {error}")
    return errors
