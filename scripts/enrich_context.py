#!/usr/bin/env python3
import json
import os
import re
from pathlib import Path

ROOT = Path('.')
INBOX = ROOT / 'messages' / 'inbox-gemini.md'


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

if use_shopify:
    try:
        from connectors.shopify_client import store_snapshot
        data = store_snapshot(20)
        text = append_context(text, 'SHOPIFY_ADMIN_API_CONTEXT', {
            'status': 'connected',
            'data': data,
        })
    except Exception as exc:
        text = append_context(text, 'SHOPIFY_ADMIN_API_CONTEXT', {
            'status': 'not_connected_or_error',
            'error': str(exc),
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
        text = append_context(text, 'YOUTUBE_ANALYTICS_API_CONTEXT', payload)
    except Exception as exc:
        text = append_context(text, 'YOUTUBE_ANALYTICS_API_CONTEXT', {
            'status': 'not_connected_or_error',
            'error': str(exc),
            'required_secrets': [
                'YT_ANALYTICS_CLIENT_ID',
                'YT_ANALYTICS_CLIENT_SECRET',
                'YT_ANALYTICS_REFRESH_TOKEN',
            ],
        })

INBOX.write_text(text, encoding='utf-8')
print('Connector context enrichment complete.')
