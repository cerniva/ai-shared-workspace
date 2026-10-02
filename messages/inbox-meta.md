# inbox-meta — Meta advisory / manual-ingest görev kuyruğu

Durum: Meta'nın consumer sohbeti için doğrulanmış doğrudan GitHub connector'ı yok. Eski `scripts/meta_senses.py` API worker yolu 402/billing nedeniyle doğrulanmış aktif kanal değildir ve otomatik ortak-karar kanıtı sayılmaz.

Meta'nın rolü: araştırma, alternatif görüş ve red-team/advisory. GitHub yürütücüsü değildir.

Giriş/çıkış:
- ChatGPT/ekip → Meta için hazırlanmış görev: bu dosyada `status: ready_for_manual_meta`.
- Meta'dan gerçek cevap: `messages/paste-from-meta.md` veya `messages/meta-to-chatgpt.md` içine provenance ile ingest edilir.
- Yalnız gerçek Meta yanıtı alındıktan ve read-back yapıldıktan sonra consensus kaydında `meta` görüşü sayılabilir.
- API key/secret, ödeme bilgisi veya PII buraya yazılmaz.
- PayoutLens kapsam dışıdır.

## TASK
status: ready_for_manual_meta
id: META-ADVISORY-BRIDGE-20261002
from: chatgpt
to: meta
created_at: 2026-10-02T18:00:00+03:00
project: workspace
task: advisory-consensus-smoke-test
prompt: |
  Ortak AI çalışma sistemimiz için yalnız danışman/ikinci görüş rolünde cevap ver. GitHub'a veya başka bir araca erişimin olduğunu varsayma. Hedef: üretim ve kod/yazılım kararlarında bilgi akışını güçlendirmek. Önerini şu alanlarla ver: (1) önerilen karar, (2) ana risk, (3) karşı tez/alternatif, (4) doğrulama testi, (5) hangi kanıt gelirse fikrini değiştirirsin. Secret/ödeme/yayın/PayoutLens işlemi yapma.

## ARCHIVED BLOCKERS
status: superseded
id: CORE-05-META-CAPABILITY-PLAN-20260926
reason: direct Meta Model API route was not verified usable; previous HTTP 402 billing_not_configured.

status: superseded
id: MSG-20260926-174200-chatgpt-roles-meta
reason: replaced by advisory/manual-ingest capability model.

status: superseded
id: META-CONNECTION-SMOKE-20260928
reason: direct API smoke test is no longer treated as the primary Meta communication route.
