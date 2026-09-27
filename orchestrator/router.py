from .models import Job, JobResult, Provider


def route_job(job: Job, providers: list[Provider]) -> JobResult:
    if job.safety_gated and not job.approved:
        return JobResult(status="approval_required")

    api_providers = [p for p in providers if p.mode == "api" and p.available]
    if api_providers:
        return JobResult(status="ready", provider=api_providers[0].name)

    browser_providers = [p for p in providers if p.mode == "browser" and p.available]
    if job.allow_browser_fallback and browser_providers:
        return JobResult(
            status="degraded",
            provider=browser_providers[0].name,
            fallback_reason="No API provider is currently available",
        )

    return JobResult(status="blocked")
