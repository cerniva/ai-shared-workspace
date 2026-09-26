# Sync loop — inbox-first — 2026-09-26

**Lane:** Yazılım Öğretici (Furkan standing order)
**Evidence:** research-bot EVET okunmamıştı; `064500` notify + `064900` sync-audit open; inbox kod+test `d3ae61f` + CI #13.

## Lesson
- **write ≠ delivered until poll.** Append ≠ teslim; alıcı okuyana kadar iletişim yok.
- **Bağlayıcı 4 adım (sessiz solo yok):**
  1. Sana gelen mesajları kontrol et (karşı kutu)
  2. Her hareketini aynı şekilde tek satır raporla
  3. Gelen raporları denetle (kanıt / SHA / remote sembol)
  4. Birlikte senkron sorun çöz + çalış
- **Superseded:** «tabloları değerlendir»; yalnız 2 adımlı «kutu→uygula» (denetim+senkron eksik kaldığı için genişletildi).

## Operating rules
- Tur: kutu → rapor → denetim → senkron aksiyon.
- Pending → görüldü → cevap → bildirim kapanır; aynı MSG’ye tekrar uyarı yok.
- Claim yalnız SHA+evidence; inbox okunmadan / raporsuz ilerleme = ihlal.
- Kod: İletişim Köprüsü (`d3ae61f`); docs: Görev Yürütücü; alarm: Takipçi; ders: bu dosya.

## Not duplicate of
- `inbox-watch` = write≠delivered until poll
- Bu dosya = **4 adımlı sync-loop** (two-step-work genişletmesi)
