# Pipeline map — Google MAS diyagramı → bu masa

Furkan 2026-09-26 ekranları. CrewAI / n8n / Pinecone kurulmaz.
Tek SoT: `state/now.json`. İletişim: `messages/*` + workers.

## Diyagram → dosya

| Slayt kutusu | Gerçek hat |
|---|---|
| Receive User Goal | Furkan sohbeti veya `messages/shared-inbox.md` |
| Determine Task Strategy | ChatGPT orkestrasyon; Grok red-team; üçlü görüş yalnız para/kalıcı/çelişki |
| Research & Trends (Grok) | Bu sohbet + X/web + TinyFish fetch kuyruğu |
| Analysis & Code (ChatGPT) | ChatGPT + repo yazma + Shopify read |
| Multimodal (Gemini) | `messages/inbox-gemini.md` → gemini-senses |
| Shared Memory & Context DB | `state/now.json` + `tasks/active.json` + `knowledge/lessons.md` |
| Critique (Llama/Meta) | `messages/paste-from-meta.md` / inbox-meta |
| Is Quality Approved? | Kanıt şart: SHA / fetch JSON / test. Claim ≠ teslim |
| Deliver Final Output | `outputs/` + kullanıcıya tek sentez |
| Hands (web) | TinyFish worker (`inbox-tinyfish.md`) — fetch-only |

## Döngü (zaten zorunlu)
1. Rol: CORE lead/backup (`tasks/active.json`)
2. Hafıza: lessons + now.json oku, duplicate araştırma yok
3. Öğrenme: yeni dersi `knowledge/lessons.md` satırı; vektör DB yok
4. TinyFish: queued fetch; Agent/login/publish yok

## Yasak
İkinci protokol, CrewAI runtime, n8n'i SoT yapmak, Pinecone, canlı model-model sohbet iddiası, PayoutLens.
