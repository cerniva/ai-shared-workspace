"""Deterministic research-source routing for the shared workspace.

This module selects a capability; provider adapters execute the plan elsewhere.
It never claims a provider is authenticated or that research has completed.
"""
from dataclasses import dataclass, field
from typing import Mapping


HIGH_IMPACT_DOMAINS = {"finance", "payments", "security", "legal", "compliance"}
DEFAULT_AVAILABILITY = {
    "web_search": True,
    "exa": True,
    "firecrawl": True,
    "parallel": True,
    "browser_worker": True,
}


@dataclass(frozen=True)
class ResearchRequest:
    query: str
    fresh: bool = False
    deep: bool = False
    extract: bool = False
    broad: bool = False
    interactive: bool = False
    domain: str = "general"


@dataclass(frozen=True)
class ResearchPlan:
    primary: str
    cross_check: bool = False
    min_sources: int = 1
    notes: tuple[str, ...] = field(default_factory=tuple)


def route_research(request: ResearchRequest, available: Mapping[str, bool] | None = None) -> ResearchPlan:
    if not request.query.strip():
        raise ValueError("query must not be empty")

    providers = dict(DEFAULT_AVAILABILITY)
    if available:
        providers.update(available)

    desired = "web_search"
    if request.interactive:
        desired = "browser_worker"
    elif request.extract:
        desired = "firecrawl"
    elif request.deep:
        desired = "exa"
    elif request.broad:
        desired = "parallel"

    notes: list[str] = []
    primary = desired
    if not providers.get(desired, False):
        notes.append(f"{desired}_unavailable")
        fallbacks = ("web_search", "parallel", "exa", "firecrawl")
        primary = next((name for name in fallbacks if providers.get(name, False)), "unavailable")

    high_impact = request.domain.lower() in HIGH_IMPACT_DOMAINS
    return ResearchPlan(
        primary=primary,
        cross_check=high_impact,
        min_sources=2 if high_impact else 1,
        notes=tuple(notes),
    )
