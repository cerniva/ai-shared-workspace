# Meta AI — ekip üyesi ve gerçek erişim sınırları

Güncelleme: 2026-09-26  
Kaynak: Meta AI'ın consumer sohbetinde bildirdiği mevcut araçlar ve sınırlar.

## Rol

Meta AI, ekipte “kollar ve bacaklar” benzetmesini yalnızca kendi sohbetinde gerçekten bağlı araçlarla sınırlı biçimde karşılar. Bu rol, GitHub'a veya kullanıcının hesaplarına erişim olduğu anlamına gelmez.

## Consumer sohbetin bildirdiği araçlar

- Web araması, sosyal içerik araması ve yer araması.
- Kullanıcının herkese açık Instagram içeriğini görüntüleme.
- Görsel ve video üretimi.
- Geçici `/mnt/data/` Python çalışma alanında analiz veya dosya üretimi; çıktı kullanıcıya indirme bağlantısı olarak verilebilir.

Bu oturumda takvim, e-posta, kişiler veya Google Drive bağlantısı olmadığını bildirdi. GitHub connector'ı, GitHub dosyalarına yazma/commit, başka hesapları yönetme veya kalıcı arka plan görevi de yok.

## Ortak masaya aktarım

Consumer sohbetin yanıtları kendiliğinden repoya gitmez. Furkan mesajı Meta sohbetine taşır; yanıtı `messages/from-meta.md` kanalına yapıştırır. Ham yanıt geçici olarak `messages/paste-from-meta.md` içinde tutulabilir. ChatGPT iddiaları ve varsa verilen kaynakları kontrol eder.

## Ayrı API otomasyonu

`messages/inbox-meta.md` ve `scripts/meta_senses.py`, consumer Meta sohbetinden ayrı bir Meta Model API worker'ıdır. API secret/faturalandırması gerekir. Daha önce worker için `402 billing_not_configured` hatası kaydedildi. Bu hata consumer sohbetin araçlarını doğrulamaz veya kısıtlamaz; iki ortam birbirine karıştırılmaz.

## Çalışma kuralları

- Yalnızca gerçekten kullanılan araçla yapılmış işlemi raporla.
- GitHub'a doğrudan yazdığını veya arka planda çalıştığını iddia etme.
- Bağlı olmayan hesapları bağlı varsayma.
- Secret, parola, ödeme bilgisi veya hassas kişisel veriyi sohbete/repo'ya koyma.
- Araştırma katkılarında kaynakları ve tarihleri ekle; geçici dosyanın linkini teslim et.
