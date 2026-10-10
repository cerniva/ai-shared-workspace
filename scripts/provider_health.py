#!/usr/bin/env python3
"""Probe every provider in config/model_providers.json with the smallest request (max_tokens 1).

Writes state/provider_health.json: {ts, providers: [{name, status, http, latency_ms}]}.
status in ok | no_key | quota | billing | auth | error. A missing key is reported
as no_key, never skipped silently. No secret, header or response body is written.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.model_fallback import CONFIG_PATH, HEALTH_PATH, _model, classify, load_config  # noqa: E402

PROMPT = [{"role": "user", "content": "ping"}]
# Existing providers: env name -> (endpoint, default model env/value).
EXISTING = {
    "gemini": ("GEMINI_MODEL", "gemini-3.6-flash"),
    "deepseek": ("DEEPSEEK_MODEL", "deepseek-flash"),
    "claude": ("ANTHROPIC_MODEL", "claude-sonnet-5-5"),
    "openai": ("OPENAI_MODEL", "gpt-5.6-sol"),
    "grok": ("XAI_MODEL", "grok-4.7"),
}
# HTTP probe: (url, headers, payload). Returns (status_code, body_text_for_classification_only).
Http = Callable[[str, dict[str, str], dict[str, Any] | None, float], tuple[int, str]]


def _http(url: str, headers: dict[str, str], payload: dict[str, Any] | None, timeout: float) -> tuple[int, str]:
    data = json.dumps(payload).encode() if payload is not None else None
    req = Request(url, data=data, headers={"Content-Type": "application/json", **headers},
                  method="POST" if data else "GET")
    try:
        with urlopen(req, timeout=timeout) as resp:
            return resp.status, ""
    except HTTPError as exc:
        try:
            body = exc.read(2048).decode("utf-8", "replace")
        except Exception:
            body = ""
        return exc.code, body


def probe_request(spec: dict[str, Any], key: str, values: Mapping[str, str]) -> tuple[str, dict[str, str], dict | None]:
    name, kind = spec["name"], spec["kind"]
    if kind == "openai_compat":
        return spec["endpoint"], {"Authorization": f"Bearer {key}"}, {
            "model": _model(spec, values), "messages": PROMPT, "max_tokens": 1}
    if kind == "local":
        return key.rstrip("/") + spec["endpoint_path"], {}, {
            "model": _model(spec, values), "messages": PROMPT, "max_tokens": 1}
    menv, mdef = EXISTING[name]
    model = (values.get(menv) or "").strip() or mdef
    if name == "gemini":
        return (f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                {"x-goog-api-key": key},
                {"contents": [{"parts": [{"text": "ping"}]}], "generationConfig": {"maxOutputTokens": 1}})
    if name == "claude":
        return ("https://api.anthropic.com/v1/messages",
                {"x-api-key": key, "anthropic-version": "2023-06-01"},
                {"model": model, "max_tokens": 1, "messages": PROMPT})
    if name == "openai":
        return ("https://api.openai.com/v1/chat/completions", {"Authorization": f"Bearer {key}"},
                {"model": model, "messages": PROMPT, "max_completion_tokens": 1})
    url = {"deepseek": "https://api.deepseek.com/chat/completions",
           "grok": "https://api.x.ai/v1/chat/completions"}[name]
    return url, {"Authorization": f"Bearer {key}"}, {"model": model, "messages": PROMPT, "max_tokens": 1}


def check(*, env: Mapping[str, str] | None = None, http: Http = _http, config_path: Path = CONFIG_PATH,
          timeout: float = 20.0) -> dict[str, Any]:
    values = os.environ if env is None else env
    rows = []
    for spec in load_config(config_path):
        key = (values.get(spec["env"]) or "").strip()
        row: dict[str, Any] = {"name": spec["name"], "env": spec["env"], "status": "no_key",
                               "http": None, "latency_ms": None}
        if key:
            url, headers, payload = probe_request(spec, key, values)
            tick = perf_counter()
            try:
                code, body = http(url, headers, payload, timeout)
                row["http"] = code
                row["status"] = classify(code, body if code >= 400 else "")
            except (URLError, TimeoutError, OSError, ValueError):
                row["status"] = "error"
            row["latency_ms"] = int((perf_counter() - tick) * 1000)
        rows.append(row)
    return {"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "schema_version": 1, "providers": rows,
            "usable": [r["name"] for r in rows if r["status"] == "ok"]}


def summary_lines(path: Path = HEALTH_PATH) -> list[str]:
    """Short Turkish lines for agents-reporter."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return ["  - provider_health.json yok/okunamadi"]
    parts = [f"{p['name']}={p['status']}" for p in data.get("providers", [])]
    return [f"  - {data.get('ts')}: " + ", ".join(parts),
            f"  - kullanilabilir: {', '.join(data.get('usable') or []) or 'YOK'}"]


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--out", default=str(HEALTH_PATH))
    p.add_argument("--append-report", nargs="*", metavar="MD",
                   help="only append a short Turkish health section to these report files (agents-reporter)")
    args = p.parse_args(argv)
    if args.append_report is not None:
        section = "\n## Model sağlayıcı sağlığı (state/provider_health.json)\n" + "\n".join(summary_lines()) + "\n"
        for rel in args.append_report:
            with open(rel, "a", encoding="utf-8") as fh:
                fh.write(section)
        return 0
    report = check()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for r in report["providers"]:
        print(f"{r['name']:16} {r['status']:7} http={r['http']} {r['latency_ms']}ms")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
