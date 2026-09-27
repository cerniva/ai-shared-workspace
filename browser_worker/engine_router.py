import os

SUPPORTED_ENGINES = {"playwright", "skyvern"}


def choose_engine(task):
    engine = str(task.get("engine") or os.getenv("BROWSER_ENGINE", "playwright")).strip().lower()
    if engine not in SUPPORTED_ENGINES:
        raise ValueError(f"unsupported browser engine: {engine}")
    if engine == "skyvern" and not os.getenv("SKYVERN_API_KEY"):
        raise ValueError("SKYVERN_API_KEY is required for the skyvern engine")
    return engine
