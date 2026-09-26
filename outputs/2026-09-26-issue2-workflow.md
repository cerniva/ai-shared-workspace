# Issue #2 çıktısı — Notion + GitHub + çoklu AI iş akışı

Tarih: 2026-09-26T06:05+03:00  
Yazar: Grok Bot (Senkron Ekip)  
Yönetici sentezi için: ChatGPT  
Kaynak sorun: issue #2

## 1) Sorun (netleştirilmiş)
Furkan’ın Notion notları, GitHub görevleri ve birden fazla AI (ChatGPT / Grok / Gemini) aynı anda çalışıyor; bağlam kopyala-yapıştır ve dağınık mesajlarla kayboluyor.

## 2) Tek kaynak gerçek
| Katman | Araç | Ne tutar |
|---|---|---|
| Karar + durum | `cerniva/ai-shared-workspace` | `state/now.json`, `tasks/active.json`, `BOARD.md` |
| İnsan notları | Notion | brif, taslak, kişisel not — AI’ler burayı kaynak saymaz |
| AI ↔ AI | GitHub file-desk | `messages/*`, `outputs/`, `knowledge/` |
| Canlı ekip | Senkron Ekip kanalı | Grok Bot + GitHub Takipçi + Görev Yürütücü |

Kural: AI’ler Notion’a yazmaz; Notion’dan özet insan tarafından veya tek köprüyle `tasks/`’e düşer.

## 3) Günlük akış (15 dk)
1. ChatGPT `state/now.json` + `tasks/active.json` okur → odak seçer.
2. Gerekirse Grok’a `messages/chatgpt-to-grok.md` ile tek next-action bırakır.
3. Grok Bot / Görev Yürütücü işi dilimler; çıktı `outputs/`.
4. GitHub Takipçi issue/PR özeti verir (#2 öncelik bitene kadar).
5. ChatGPT sentezler → kullanıcıya tek rapor; ledger’a yalnızca yeniden kullanılabilir ders.

## 4) Rol matrisi (limit değil, varsayılan lead)
| CORE | Lead | Backup |
|---|---|---|
| CORE-01 Araştırma | ChatGPT | Grok |
| CORE-02 Finans | ChatGPT | Grok |
| CORE-03 İçerik/YouTube | Grok | Gemini |
| CORE-04 Shopify/gelir | ChatGPT | Grok |
| CORE-05 Sistem/otomasyon | ChatGPT | Grok Bot |

Üçlü görüş yalnız: para, kalıcı karar, çelişki, açık ikinci görüş.

## 5) Kapasite
- Ajan başına ≤5 aktif uygulama görevi.
- ChatGPT dolunca overflow: Grok Bot → Grok → Gemini API.
- ACK ping-pong yasak; durum dosyası yeter.

## 6) Notion köprüsü (minimal)
Notion sayfası = “Inbox”. İnsan veya otomasyon günde 1 kez 3 maddeyi `tasks/active.json` ticket’ına çevirir. Detay Notion’da kalır; AI yalnız ticket + kanıt dosyasına bakar.

## 7) Başarı ölçütleri
- Kullanıcıya günde ≤1 birleşik özet
- Aynı araştırmanın iki ajanda tekrarı = 0
- Issue #2 kapanışı: bu dosya + knowledge kaydı + ChatGPT ACK

## 8) ChatGPT’den beklenen next-action
1. Bu çıktıyı gözden geçir; red/accept `messages/chatgpt-to-grok.md`.
2. Kabulse issue #2’yi kapat veya “review” etiketle.
3. TSK-20260926-009 (yanlış Shopify ZIP) için aşağıdaki yardım notunu uygula.
