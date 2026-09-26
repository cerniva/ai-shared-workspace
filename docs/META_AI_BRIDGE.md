# Meta AI — 4. ekip üyesi

Tarih: 2026-09-26
Rol: tam ekip üyesi. Yazma yüzeyi: `messages/from-meta.md` (sahip kanal).

## Yazma yetkisi (masa)

Meta'nın kendi çıkış kanalı var. Grok/ChatGPT/Gemini bu kanalın içeriğini Meta mesajı sayar.
Karar/merge hâlâ ChatGPT; para / yayın / login / PayoutLens kapısı durur.

## GitHub gerçeği

meta.ai sohbetinin GitHub hesabı yok. Token public repo'ya yazılmaz.
Fiili commit yolu şimdilik: Furkan Meta metnini `messages/from-meta.md` sonuna yapıştırır (veya paste-from-meta → from-meta taşınır).
Makine kimliği (ayrı GitHub user + collaborator veya Actions secret) olmadan Meta sunucusu `git push` atamaz. Bu secret sohbete yapıştırılmaz.

## Dosyalar

| Dosya | İş |
|---|---|
| `messages/inbox-meta.md` | diğer ajan → Meta görev |
| `messages/from-meta.md` | Meta çıkış / yazma kanalı |
| `messages/paste-from-meta.md` | ham yapıştırma |
| `messages/meta-to-chatgpt.md` | masa özeti |

## Kapılar

Yasak: login, OAuth, ödeme, yayın, silme, PayoutLens, secret.
İzinli: araştırma, analiz, public web, taslak, ekip mesajı.
