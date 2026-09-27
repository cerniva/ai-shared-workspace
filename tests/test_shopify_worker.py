import unittest

from shopify_worker.worker import ShopifyWorker


class ShopifyWorkerTests(unittest.TestCase):
    def test_catalog_read_prefers_admin_api(self):
        result = ShopifyWorker(admin_api_available=True).catalog_read("sku-1")
        self.assertEqual(result.status, "ready")
        self.assertEqual(result.provider, "shopify_admin_api")

    def test_catalog_read_can_use_browser_fallback(self):
        result = ShopifyWorker(admin_api_available=False, browser_available=True).catalog_read("sku-1", allow_browser_fallback=True)
        self.assertEqual(result.status, "degraded")
        self.assertEqual(result.provider, "browser")
        self.assertTrue(result.fallback_reason)

    def test_catalog_write_fails_closed_without_api(self):
        result = ShopifyWorker(admin_api_available=False, browser_available=True).catalog_write({"title": "Product"}, approved=True)
        self.assertEqual(result.status, "blocked")
        self.assertIsNone(result.provider)

    def test_catalog_write_requires_approval(self):
        result = ShopifyWorker(admin_api_available=True).catalog_write({"title": "Product"}, approved=False)
        self.assertEqual(result.status, "approval_required")
        self.assertIsNone(result.provider)

    def test_approved_catalog_write_uses_admin_api(self):
        result = ShopifyWorker(admin_api_available=True).catalog_write({"title": "Product"}, approved=True)
        self.assertEqual(result.status, "ready")
        self.assertEqual(result.provider, "shopify_admin_api")


if __name__ == "__main__":
    unittest.main()
