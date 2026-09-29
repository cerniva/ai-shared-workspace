from scripts.provider_router import ProviderCandidate, select_provider


def test_free_first_order():
    candidates = [
        ProviderCandidate("paid", "paid", True),
        ProviderCandidate("cloud", "cloud_free", True),
        ProviderCandidate("local", "local_free", True),
    ]
    assert select_provider(candidates).name == "local"


def test_paid_requires_explicit_opt_in():
    candidates = [ProviderCandidate("paid", "paid", True)]
    assert select_provider(candidates) is None
    assert select_provider(candidates, allow_paid=True).name == "paid"


def test_unhealthy_and_auth_blocked_are_skipped_without_retry():
    candidates = [
        ProviderCandidate("local", "local_free", False),
        ProviderCandidate("authbad", "cloud_free", True, failure_class="auth"),
        ProviderCandidate("fallback", "cloud_free", True),
    ]
    assert select_provider(candidates).name == "fallback"
