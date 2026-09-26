#!/usr/bin/env python3
import json
import os
import urllib.parse
import urllib.request

API_VERSION = os.environ.get("SHOPIFY_API_VERSION", "2026-07").strip()
SHOP = os.environ.get("SHOPIFY_STORE", "").strip().replace("https://", "").replace("http://", "")
CLIENT_ID = os.environ.get("SHOPIFY_CLIENT_ID", "").strip()
CLIENT_SECRET = os.environ.get("SHOPIFY_CLIENT_SECRET", "").strip()

class ShopifyError(RuntimeError):
    pass

def _shop_host() -> str:
    if not SHOP:
        raise ShopifyError("SHOPIFY_STORE secret eksik.")
    return SHOP if SHOP.endswith(".myshopify.com") else f"{SHOP}.myshopify.com"

def access_token() -> str:
    if not CLIENT_ID or not CLIENT_SECRET:
        raise ShopifyError("SHOPIFY_CLIENT_ID / SHOPIFY_CLIENT_SECRET secret eksik.")
    body = urllib.parse.urlencode({
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }).encode("utf-8")
    req = urllib.request.Request(
        f"https://{_shop_host()}/admin/oauth/access_token",
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            data = json.loads(r.read().decode("utf-8"))
    except Exception as exc:
        raise ShopifyError(f"Shopify token alınamadı: {exc}") from exc
    token = data.get("access_token")
    if not token:
        raise ShopifyError(f"Shopify token yanıtı geçersiz: {data}")
    return token

def graphql(query: str, variables: dict | None = None) -> dict:
    token = access_token()
    payload = json.dumps({"query": query, "variables": variables or {}}).encode("utf-8")
    req = urllib.request.Request(
        f"https://{_shop_host()}/admin/api/{API_VERSION}/graphql.json",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "X-Shopify-Access-Token": token,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.loads(r.read().decode("utf-8"))
    except Exception as exc:
        raise ShopifyError(f"Shopify GraphQL çağrısı başarısız: {exc}") from exc
    if data.get("errors"):
        raise ShopifyError(json.dumps(data["errors"], ensure_ascii=False))
    return data.get("data") or {}

def store_snapshot(first: int = 20) -> dict:
    q = """
    query StoreSnapshot($first: Int!) {
      shop { name currencyCode myshopifyDomain }
      products(first: $first, sortKey: UPDATED_AT, reverse: true) {
        nodes {
          id title handle status vendor productType updatedAt
          totalInventory
          variants(first: 10) { nodes { id title sku price inventoryQuantity } }
        }
      }
      orders(first: 10, sortKey: CREATED_AT, reverse: true) {
        nodes { id name createdAt displayFinancialStatus displayFulfillmentStatus totalPriceSet { shopMoney { amount currencyCode } } }
      }
    }
    """
    return graphql(q, {"first": max(1, min(first, 50))})
