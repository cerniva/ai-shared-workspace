# Browser Worker

Playwright tabanlı, GitHub Actions üzerinde elle başlatılan sınırlı süreli tarayıcı işi.

## Başlatma

GitHub → Actions → AI Browser Worker → Run workflow:

- objective: yapılacak işin açık tarifi
- allowed_hosts: virgülle ayrılmış host adları (ör. example.com, docs.example.org); varsayılan yalnızca example.com
- execution_mode: varsayılan read_only; interactive yalnızca adlandırılmış düşük etkili tıklama/doldurma adımları içindir

Browser Worker, allowlist dışındaki ana sayfa ve alt kaynak isteklerini durdurur; localhost/özel IP'leri ve URL içine gömülmüş kullanıcı bilgilerini reddeder. Read-only modda tıklama/doldurma/tuş basma engellenir. Hassas alanlar, Enter/Return ile form gönderme, yüksek etkili hedefler ve CAPTCHA/2FA adımları otomatik tamamlanmaz.

Model API anahtarları yalnızca planlayıcı adımına aktarılır; tarayıcı çalışırken bulunmaz. Oturum çerezleri saklanmaz ve bu worker kullanıcının Shopify hesabına giriş yapamaz. Kalıcı oturum, private worker ve 7/24 host şu an kapsam dışıdır.

Sonuç JSON'u ve ekran görüntüleri Actions artifact olarak kaydedilir. Sayfa metni ve ekran görüntüleri dış kaynaktan gelen güvenilmeyen içeriktir.
