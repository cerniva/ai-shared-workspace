#!/usr/bin/env python3
import datetime as dt
import json
import os
import re
from pathlib import Path

ROOT = Path('.')
INBOX = ROOT / 'messages' / 'inbox-gemini.md'
HEALTH = ROOT / 'state' / 'connector-health.json'


def field(text: str, name: str, default: str = '') -> str:
    m = re.search(rf'(?mi)^\s*{re.escape(name)}\s*:\s*(.*?)\s*$', text)
    return m.group(1).strip() if m else default


def truthy(value: str) -> bool:
    return value.strip().lower() in {'1', 'true', 'yes', 'on', 'evet'}


def append_context(text: str, title: str, payload) -> str:
    if isinstance(payload, str):
        body = payload
    else:
        body = json.dumps(payload, ensure_ascii=False, indent=2)
    return text.rstrip() + f'\n\n## {title}\n```json\n{body}\n```\n'


text = INBOX.read_text(encoding='utf-8')
project = field(text, 'project', 'workspace')
use_shopify = truthy(field(text, 'use_shopify', 'false'))
use_yt_analytics = truthy(field(text, 'use_youtube_analytics', 'false'))
video_id = field(text, 'video_id', '')

health = {
    'updated_at': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
    'project': project,
    'shopify': {'status': 'not_requested'},
    'youtube_analytics': {'status': 'not_requested'},
}

if use_shopify:
    try:
        from connectors.shopify_client import store_snapshot
        data = store_snapshot(20)
        shop = data.get('shop') or {}
        products = ((data.get('products') or {}).get('nodes') or [])
        orders = ((data.get('orders') or {}).get('nodes') or [])
        shopify_payload = {
            'status': 'connected',
            'data': data,
        }
        health['shopify'] = {
            'status': 'connected',
            'shop_name': shop.get('name'),
            'currency': shop.get('currencyCode'),
            'myshopify_domain': shop.get('myshopifyDomain'),
            'product_count_in_snapshot': len(products),
            'order_count_in_snapshot': len(orders),
        }
        text = append_context(text, 'SHOPIFY_ADMIN_API_CONTEXT', shopify_payload)
    except Exception as exc:
        err = str(exc)
        health['shopify'] = {'status': 'error', 'error': err}
        text = append_context(text, 'SHOPIFY_ADMIN_API_CONTEXT', {
            'status': 'not_connected_or_error',
            'error': err,
            'required_secrets': ['SHOPIFY_STORE', 'SHOPIFY_CLIENT_ID', 'SHOPIFY_CLIENT_SECRET'],
        })

if use_yt_analytics:
    try:
        from connectors.youtube_analytics_client import channel_overview, video_retention
        payload = {
            'status': 'connected',
            'channel_overview_28d': channel_overview(28),
        }
        if video_id:
            payload['video_retention'] = video_retention(video_id)
        health['youtube_analytics'] = {'status': 'connected'}
        text = append_context(text, 'YOUTUBE_ANALYTICS_API_CONTEXT', payload)
    except Exception as exc:
        err = str(exc)
        health['youtube_analytics'] = {'status': 'error', 'error': err}
        text = append_context(text, 'YOUTUBE_ANALYTICS_API_CONTEXT', {
            'status': 'not_connected_or_error',
            'error': err,
            'required_secrets': [
                'YT_ANALYTICS_CLIENT_ID',
                'YT_ANALYTICS_CLIENT_SECRET',
                'YT_ANALYTICS_REFRESH_TOKEN',
            ],
        })

HEALTH.parent.mkdir(parents=True, exist_ok=True)
HEALTH.write_text(json.dumps(health, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
INBOX.write_text(text, encoding='utf-8')
print('Connector context enrichment complete.')
