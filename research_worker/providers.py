from dataclasses import dataclass


@dataclass(frozen=True)
class ResearchProvider:
    name: str
    available: bool = False
    priority: int = 100
