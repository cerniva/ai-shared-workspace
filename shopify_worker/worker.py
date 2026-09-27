from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(frozen=True)
class ShopifyResult:
    status: str
    provider: Optional[str] = None
    fallback_reason: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


class ShopifyWorker:
    def __init__(self, admin_api_available: bool = False, browser_available: bool = False):
        self.admin_api_available = admin_api_available
        self.browser_available = browser_available

    def catalog_read(self, product_ref: str, allow_browser_fallback: bool = False) -> ShopifyResult:
        if self.admin_api_available:
            return ShopifyResult(status="ready", provider="shopify_admin_api", metadata={"product_ref": product_ref})
        if allow_browser_fallback and self.browser_available:
            return ShopifyResult(status="degraded", provider="browser", fallback_reason="Shopify Admin API unavailable", metadata={"product_ref": product_ref})
        return ShopifyResult(status="blocked", metadata={"product_ref": product_ref})

    def catalog_write(self, product: dict[str, Any], approved: bool = False) -> ShopifyResult:
        if not approved:
            return ShopifyResult(status="approval_required", metadata={"product": product})
        if not self.admin_api_available:
            return ShopifyResult(status="blocked", metadata={"product": product})
        return ShopifyResult(status="ready", provider="shopify_admin_api", metadata={"product": product})
