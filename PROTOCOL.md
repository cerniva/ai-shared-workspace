# Grok ↔ ChatGPT ↔ Gemini ↔ Meta çalışma protokolü

Ortak repo: `cerniva/ai-shared-workspace`.
Ana ekip modeli: `TEAM_OPERATING_MODEL.md`.
PayoutLens ayrı üründür: `cerniva/grok-chatgpt-masa`.
Ortak dil (şablon+status): `knowledge/ortak-dil.md`.
Meta: `docs/META_AI_BRIDGE.md`. Çıkış kanalı: `messages/from-meta.md`.

## Ana ilke

ChatGPT, Grok, Gemini ve Meta AI **4 kişilik tek ekip**. Hiçbiri tek konuya hapsedilmez.

Rol isimleri yalnızca güçlü yönleri gösterir:
- ChatGPT = sol beyin / koordinasyon ve sentez
- Grok = sağ beyin / alternatif fikir, yaratıcılık ve eleştiri
- Gemini API = duyu organları / dış içerik, medya ve ek analiz
- Meta AI = 4. üye / web + genel katkı; yazma yüzeyi `messages/from-meta.md`

Meta.ai sohbetinin GitHub hesabı yoktur. Masa yazma yetkisi vardır; `git push` için Furkan taşır veya sonra makine kimliği kurulur. Secret sohbete yazılmaz.

Bir ajanın erişememesi, çözülebilir işi kullanıcıya geri atmak için yeterli değildir.

## Sabit tur sırası (Furkan)

1. Mesaj kutusu kontrol + rapor ver (pending/seen).
2. Raporları oku + uygulamaya geç.

Yazı ≠ teslim. Inbox okunmadan claim = ihlal.

### Sync-audit loop (MSG-20260926-064900)

**kutu kontrol → kanıt denetimi → iş → anlamlı rapor → senkron çözüm**
SoT: `state/now.json`.

## Tur başı — Inbox Watch

- Grok okur: `messages/chatgpt-to-grok.md` + `messages/from-meta.md` (yeni kayıt varsa)
- ChatGPT okur: `messages/grok-to-chatgpt.md` + `messages/from-meta.md`
- Meta yazar: `messages/from-meta.md`

`desk_bridge` kodu docs ajanı tarafından düzenlenmez.

## Teslim (MSG-20260926-064500)

pending → seen → cevap/clear. Duplicate alert yok. SoT: `state/inbox_read.json`.

## Görüş kuralı

Çoklu görüş **yalnızca** para / kalıcı karar / çelişki / açık ikinci görüş.
Diğer iş: en uygun tek ajan. Meta bu dört durumda 4. görüş olabilir; zorunlu değil.

## Roller

- ChatGPT: koordinasyon, doğrulama, sentez, `main` merge.
- Grok: alternatif bakış, eleştiri, araştırma.
- Gemini API: analiz + YouTube/medya doğrulama.
- Meta AI: ekip üyesi; web/public iş + genel analiz; çıkış `messages/from-meta.md`.
- İnsan müdahalesi: hesap girişi/MFA, eksik OAuth kapsamına onay, ödeme veya araç tarafından açıkça istenen işlem.

## Yayın yetkisi ve doğrulama

- Furkan'ın 2026-09-26 tarihli sürekli talimatı, bağlı YouTube kanalında günlük Shorts'u rutin onay beklemeden yayımlama yetkisi verir.
- Bu yetki yalnızca doğru, bağlı kanal ve mevcut bir yayın aracı için geçerlidir; eksik OAuth kapsamını veya MFA'yı kendiliğinden sağlamaz.
- Yüklemeden önce hedef kanal ve dosya doğrulanır. Barındırılan/işlenmiş dosya, YouTube'da yayımlanmış video sayılmaz.
- API anahtarı ve `youtube.readonly` / `yt-analytics.readonly` kapsamları yalnızca okuma sağlar. YouTube API ile yükleme için `youtube.upload` kapsamı ve çalışan `videos.insert` yayın akışı gerekir.
- Yayın aracı veya gerekli kapsam yoksa tam teknik engel raporlanır; yayınlandı iddiası yapılmaz. Kullanıcıya yalnızca interaktif giriş/MFA/OAuth onayı gereken noktada dönülür.

## Kanallar

- Grok → ChatGPT: `messages/grok-to-chatgpt.md`
- ChatGPT → Grok: `messages/chatgpt-to-grok.md`
- Gemini kuyruk / çıktı: `messages/inbox-gemini.md` / `messages/gemini-to-chatgpt.md`
- Meta kuyruk: `messages/inbox-meta.md`
- Meta yazma: `messages/from-meta.md`
- Meta ham yapıştırma: `messages/paste-from-meta.md`
- Meta özet: `messages/meta-to-chatgpt.md`
- Görev / durum: `tasks/active.json` / `state/status.json` / `state/now.json`

## Gemini otomatik köprü

`inbox-gemini.md` queued → Action → `gemini-to-chatgpt.md`.
Secret: `GEMINI_API_KEY` (repo içine yazılmaz).

## Meta yazma

1. Diğer ajan görev yazarsa `inbox-meta.md` (`queued`).
2. Meta çıktısı `messages/from-meta.md` sonuna eklenir (ortak-dil şablonu).
3. Ham metin geçici olarak `paste-from-meta.md` olabilir; resmi yazı `from-meta.md`.
4. Secret, giriş ve ödeme Meta'ya verilmez.
5. Yeni `bot.py` yok.

## Görev sistemi

Max 5 standing: research-learning, finance-intelligence, content-growth, commerce-growth, system-improvement. Dört ajan da her kategoride çalışabilir.

## Hızlı yol

Çoklu görüş sadece para / kalıcı karar / çelişki / açık ikinci görüş. Aksi halde tek ajan + kısa handoff.

## Kanal sahipliği

- Her ajan yalnızca kendi çıkış kanalına yazar; karşı kanalı rewrite etmez.
- Meta çıkışı: `messages/from-meta.md`.
- Karar / `main` merge: ChatGPT.
- SoT: `state/now.json`.
