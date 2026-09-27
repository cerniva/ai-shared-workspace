from orchestrator.models import Job, Provider
from orchestrator.router import route_job


def test_prefers_available_api_provider_over_browser():
    job = Job(kind="research", action="search")
    providers = [
        Provider(name="browser", mode="browser", available=True),
        Provider(name="exa", mode="api", available=True),
    ]
    result = route_job(job, providers)
    assert result.status == "ready"
    assert result.provider == "exa"


def test_falls_back_to_browser_when_api_unavailable_and_fallback_allowed():
    job = Job(kind="research", action="extract", allow_browser_fallback=True)
    providers = [
        Provider(name="firecrawl", mode="api", available=False),
        Provider(name="browser", mode="browser", available=True),
    ]
    result = route_job(job, providers)
    assert result.status == "degraded"
    assert result.provider == "browser"
    assert result.fallback_reason


def test_missing_credentials_fail_closed_without_browser_fallback():
    job = Job(kind="shopify", action="catalog_write", allow_browser_fallback=False)
    providers = [Provider(name="shopify_admin", mode="api", available=False)]
    result = route_job(job, providers)
    assert result.status == "blocked"
    assert result.provider is None


def test_safety_gated_job_never_routes_without_approval():
    job = Job(kind="shopify", action="publish", safety_gated=True, approved=False)
    providers = [Provider(name="shopify_admin", mode="api", available=True)]
    result = route_job(job, providers)
    assert result.status == "approval_required"
    assert result.provider is None
