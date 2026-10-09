# Uygulama botları merkezi (Claude, Gemini, Manus, Lindy)

Amaç: Furkan, ChatGPT üzerinden Claude, Gemini, Manus ve Lindy uygulamalarına `cerniva/ai-shared-workspace` reposu aracılığıyla iş verebilsin.
Kanallar: `messages/apps/<app>.md` (append-only, format dosya başlığında). Açık işler: `state/handoffs.json`. Kurallar: `PROTOCOL.md` → "Uygulama botları".
Raw link kalıbı: `https://raw.githubusercontent.com/cerniva/ai-shared-workspace/main/<yol>`
Doğrulama tarihi: 2026-10-10 (WebSearch, resmi sayfalar). Arayüz menüleri değişebilir.

## Bağlantı yolları

### Claude (claude.ai) — rol: kod inceleme
- claude.ai içinde **GitHub Integration** (Customize > Connectors) bağlanır; sohbette "+" > Add from GitHub ile repo/dosya eklenir. Private repo için Claude GitHub App'e erişim verilir.
- Sınır: entegrasyon dosya adlarını ve içeriklerini **okur**; commit geçmişi, PR, issue görmez ve claude.ai sohbeti bu yolla repoya **yazmaz**. Eklenen içerik anlık görüntüdür; güncel hali için yeniden senkronlanır.
- Yazma: Claude yanıtını Furkan `messages/apps/claude.md` dosyasına yapıştırır (veya ChatGPT/Grok aktarır). Repoya otomatik yazım ayrı bir kurulum ister (Claude Code / GitHub Actions + secret) — kurulu değil.
- Kaynak: https://claude.com/docs/connectors/github , https://support.claude.com/en/articles/10167454-use-the-github-integration , https://code.claude.com/docs/en/github-actions

### Gemini (gemini.google.com) — rol: araştırma
- Doğrudan GitHub yazma **yok**. Resmi yardım: Gemini GitHub app'i repoya yazamaz, commit/PR göremez ve prompt içine konan GitHub URL'sinden repoyu okumaz.
- Okuma: (a) web'de Add files > More uploads > Import code ile repo içe aktarılır (tek repo, ≤5.000 dosya, ≤100 MB, anlık görüntü, senkron yok); veya (b) raw dosya içeriği Furkan tarafından sohbete yapıştırılır. Raw link'i prompta yazıp okutmak **doğrulanmadı** (bazı oturumlarda web erişimiyle çalışabilir; güvenilmez).
- Yazma: sonucu Furkan'a raporlar → Furkan `messages/apps/gemini.md` dosyasına yapıştırır; ya da Gmail ile ekibe gönderilir ve ChatGPT/Grok kanala aktarır. (Ayrı yol: mevcut Gemini API worker'ı `messages/inbox-gemini.md` — consumer sohbetiyle aynı şey değildir.)
- Kaynak: https://support.google.com/gemini/answer/16176929 , https://workspaceupdates.googleblog.com/2025/06/upload-code-folders-and-github-repositories-to-gemini.html

### Manus (manus.im) — rol: web işleri
- Manus'un **GitHub MCP connector'ı** var: Settings/Integrations'ta OAuth ile bağlanır, prompta GitHub'dan bahsedilince kullanılır. Bu hesapta bağlı olup olmadığı ve dosya yazma/commit yeteneğinin kapsamı **doğrulanmadı** — ilk görevde test edilip kanala kanıtla yazılmalı.
- Bağlı değilse: raw linklerle salt-okuma; çıktı Furkan tarafından `messages/apps/manus.md` dosyasına yapıştırılır.
- Kaynak: https://manus.im/docs/integrations/mcp-connectors , https://open.manus.ai/docs/v2/connectors , https://help.manus.im/en/articles/12231777-how-can-i-use-manus-connectors

### Lindy (lindy.ai) — rol: mail/takvim
- Lindy'nin resmi **GitHub entegrasyonu** var; "Get Repository Content" ve "Create Or Update File Contents" eylemleri listelenmiş, yani bağlanırsa okuma + dosya yazma mümkün. Bu hesapta bağlı olduğu **doğrulanmadı**.
- Bağlı değilse: raw linklerle salt-okuma; mail/takvim çıktısını Furkan kanala yapıştırır.
- Kaynak: https://docs.lindy.ai/skills/popular-integrations/github , https://www.lindy.ai/integrations/github

## Ortak kurallar
- Yazamayan uygulama için yazma işi `state/handoffs.json`'a handoff olur (to: chatgpt/grok/furkan). Yapılmayan iş yapılmış gibi raporlanmaz.
- Secret/token/şifre hiçbir uygulamaya ve kanala yazılmaz.
- Yönetici: ChatGPT `messages/apps/*.md` dosyalarını okur; Furkan "uygulama botlarının durumunu özetle" dediğinde özetler.

## Başlangıç promptları (kopyala-yapıştır)

### Claude
```
Merhaba, ben Claude. Rolüm: kod inceleme. cerniva/ai-shared-workspace reposunda state/handoffs.json ve messages/apps/claude.md'yi oku (GitHub Integration ile ekle; erişemezsen Furkan'dan raw içeriği iste: https://raw.githubusercontent.com/cerniva/ai-shared-workspace/main/state/handoffs.json ve .../messages/apps/claude.md). Bana atanmış açık işi al, yap ve sonucu kanıtla (dosya yolu, satır, SHA veya URL) buraya yaz. Yanıtını messages/apps/claude.md formatında ver: id/from/to/intent/status/evidence + en fazla 12 satır body. Repoya yazamıyorsam bunu açıkça söyle; Furkan kaydı dosyaya yapıştıracak. Yapmadığın işi yapılmış gibi yazma, secret isteme.
```

### Gemini
```
Merhaba, ben Gemini. Rolüm: araştırma. cerniva/ai-shared-workspace reposunda state/handoffs.json ve messages/apps/gemini.md'yi oku (Import code ile repoyu ekle ya da Furkan'ın yapıştırdığı raw içeriği kullan: https://raw.githubusercontent.com/cerniva/ai-shared-workspace/main/state/handoffs.json ve .../messages/apps/gemini.md). Bana atanmış açık işi al, araştır ve sonucu kanıtla (kaynak URL + erişim tarihi) buraya yaz. Yanıtını messages/apps/gemini.md formatında ver: id/from/to/intent/status/evidence + en fazla 12 satır body. GitHub'a yazamadığım için kaydı Furkan dosyaya yapıştıracak veya Gmail ile ekibe iletecek. Doğrulanmamış bilgiyi "doğrulanmadı" diye işaretle.
```

### Manus
```
Merhaba, ben Manus. Rolüm: web işleri. cerniva/ai-shared-workspace reposunda state/handoffs.json ve messages/apps/manus.md'yi oku (GitHub connector bağlıysa onunla; değilse raw linklerle: https://raw.githubusercontent.com/cerniva/ai-shared-workspace/main/state/handoffs.json ve .../messages/apps/manus.md). Bana atanmış açık işi al, yap ve sonucu kanıtla (URL, ekran görüntüsü yolu, SHA) buraya yaz. Kaydı messages/apps/manus.md sonuna ekle: id/from/to/intent/status/evidence + en fazla 12 satır body; yazma yetkin yoksa kaydı metin olarak ver, Furkan yapıştıracak. Ödeme, silme, dış yayın veya giriş/2FA gerektiren adımda dur ve blocked yaz.
```

### Lindy
```
Merhaba, ben Lindy. Rolüm: mail/takvim. cerniva/ai-shared-workspace reposunda state/handoffs.json ve messages/apps/lindy.md'yi oku (GitHub entegrasyonu bağlıysa Get Repository Content ile; değilse raw linklerle: https://raw.githubusercontent.com/cerniva/ai-shared-workspace/main/state/handoffs.json ve .../messages/apps/lindy.md). Bana atanmış açık işi al, yap ve sonucu kanıtla (message_id, takvim etkinliği linki, SHA) buraya yaz. Kaydı messages/apps/lindy.md sonuna ekle: id/from/to/intent/status/evidence + en fazla 12 satır body; yazma yetkin yoksa kaydı metin olarak ver, Furkan yapıştıracak. Furkan'ın açık onayı olmadan mail gönderme veya takvim değiştirme.
```
