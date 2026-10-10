# Uygulama botları merkezi (Claude, Gemini, Manus, Lindy, Genspark, Perplexity, Zapier Agents, n8n, DeepSeek, Copilot, Mistral, Make, GitHub Copilot, OpenAI Codex, Google Jules, Claude Code Action)

Amaç: Furkan, ChatGPT üzerinden uygulama botlarına `cerniva/ai-shared-workspace` reposu aracılığıyla iş verebilsin.
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

### Genspark (genspark.ai) — rol: araştırma/rapor
- Resmi **GitHub connector** var (Skills > Connectors, OAuth). Yardım merkezi yeteneği "Review PRs, read issues, search repositories" olarak listeler; CLI belgesinde list_repos ve issue arama/oluşturma/güncelleme var. **Repo dosyası yazma/commit belgelenmemiş** → doğrulanmadı; dosya yazamaz kabul edilir.
- Bu hesapta connector'ın bağlı olduğu **doğrulanmadı**. Okuma: connector veya raw linkler. Yazma: kaydı Furkan `messages/apps/genspark.md` dosyasına yapıştırır.
- Kaynak: https://www.genspark.ai/helpcenter/connectors-and-integrations , https://www.genspark.ai/helpcenter/skills

### Perplexity (perplexity.ai) — rol: araştırma, zamanlanmış görev
- Resmi **GitHub connector** var (Pro/Max/Enterprise; Settings > Connectors > Enable, GitHub OAuth). Belgede PR durumu sorgulama ve PR'a etiket ekleme gibi eylemler örneklenir. Repo dosyası yazma/commit **doğrulanmadı**.
- Zamanlanmış iş: Perplexity Computer **Automations / Scheduled Tasks** (perplexity.ai/computer/automations) zamanlamayla veya GitHub/Gmail/Slack olayıyla çalışır; bağlı connector'ları kullanır. Computer erişimi ve bu hesapta GitHub bağlantısı **doğrulanmadı**.
- Yazma: kaydı Furkan `messages/apps/perplexity.md` dosyasına yapıştırır. (Ayrı yol: Perplexity API worker'ı `messages/inbox-perplexity.md`.)
- Kaynak: https://www.perplexity.ai/help-center/en/articles/12275669-github-connector-for-enterprise , https://www.perplexity.ai/help-center/en/articles/11521526-perplexity-tasks , https://www.perplexity.ai/hub/blog/computer-adds-automations-for-ongoing-work

### Zapier Agents (zapier.com/agents) — rol: otomasyon
- Zapier GitHub uygulamasında resmi **Get File Contents** ve **Create or Update File** (Repository, File Path, Commit Message, File Content, File SHA, Branch) eylemleri var; Agents bu GitHub eylemlerini kullanabilir. Yani bağlanırsa okuma + dosya yazma mümkün. Bu hesapta bağlantı **doğrulanmadı**.
- Kural: yazma yalnız kendi kanalına (`messages/apps/zapier-agents.md`) ve append biçiminde; `.github/`, secret ve PayoutLens'e dokunulmaz.
- Kaynak: https://zapier.com/apps/agents/integrations/github , https://zapier.com/apps/github/integrations

### n8n (n8n.io) — rol: GitHub/Gmail otomasyon
- n8n **GitHub node**'u File kaynağında Create/Edit/Get/List/Delete işlemlerini destekler (Edit, SHA'yı kendisi alır); **Gmail node**'u mesaj ve taslak (Draft Create) işlemlerini destekler. Kurulu bir n8n örneği ve credential'ları bu hesapta **doğrulanmadı**.
- Kural: workflow yalnız kendi kanalına yazar; Gmail için varsayılan **taslak** oluşturmaktır, Furkan'ın açık onayı olmadan gönderim yapmaz. Delete işlemi kullanılmaz.
- Kaynak: https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.github/ , https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.gmail/draft-operations/

### DeepSeek (chat.deepseek.com) — rol: kod/mantık
- Consumer DeepSeek sohbeti için resmi bir GitHub connector'ı **bulunamadı / doğrulanmadı**. Bulunan GitHub connector'ı (DeepSeek Harness eklentisi `kaziii/dsh-github-connector`) üçüncü taraftır ve kullanılmaz.
- Okuma: Furkan raw içeriği sohbete yapıştırır. Yazma: kaydı Furkan `messages/apps/deepseek.md` dosyasına yapıştırır. (Ayrı yol: DeepSeek API worker'ı `messages/inbox-deepseek.md`.)
- Kaynak: https://api-docs.deepseek.com/ (resmi API belgeleri; consumer GitHub entegrasyonu yok)

### Copilot (Microsoft Copilot / Microsoft 365 Copilot) — rol: Office/Outlook
- Microsoft 365 Copilot için resmi **GitHub Cloud Issues / Knowledge / Pull Requests Copilot connector**'ları var; bunlar yönetici tarafından M365 admin center'da kurulur ve GitHub verisini **salt-okuma** olarak Microsoft Graph'a indeksler. Repoya yazma **yok**. Bu tenant'ta kurulu olduğu ve consumer Copilot'ta karşılığı **doğrulanmadı**.
- Yazma: Outlook/Office çıktısını Furkan `messages/apps/copilot.md` dosyasına yapıştırır.
- Kaynak: https://learn.microsoft.com/en-us/microsoft-365/copilot/connectors/github-cloud-issues-overview , https://learn.microsoft.com/en-us/microsoft-365/copilot/connectors/github-cloud-knowledge-overview

### Mistral (Le Chat, chat.mistral.ai) — rol: genel asistan / ikinci görüş
- Mistral belgeleri connector'ları (özel MCP dahil, ör. GitHub'ın resmi MCP sunucusu `https://api.githubcopilot.com/mcp/` + Bearer PAT) API/Studio tarafında anlatır. Le Chat arayüzünde GitHub connector'ının varlığı ve yazma kapsamı **doğrulanmadı**; PAT sohbete yazılmaz.
- Okuma: connector bağlıysa onunla, değilse raw içerik yapıştırılır. Yazma: kaydı Furkan `messages/apps/mistral.md` dosyasına yapıştırır.
- Kaynak: https://docs.mistral.ai/studio/connectors/conversations , https://docs.mistral.ai/resources/cookbooks/mistral-connectors-06-multiple-authentication

### Make (make.com) — rol: otomasyon
- Make'in resmi **GitHub app**'i var (issue/yorum vb. modüller). Hazır bir "dosya oluştur/güncelle" modülü **doğrulanmadı**; dosya yazma gerekiyorsa genel API çağrısı modülüyle GitHub Contents API kullanmak gerekir (doğrulanmadı). Bu hesapta bağlantı **doğrulanmadı**.
- Yazma: senaryo kendi kanalına yazamıyorsa kaydı Furkan `messages/apps/make.md` dosyasına yapıştırır.
- Kaynak: https://apps.make.com/github

### GitHub Copilot (github.com) — rol: GitHub'da kod/PR
- Resmi **Copilot cloud agent (coding agent)**: bir issue Copilot'a atanınca ayrı branch'te çalışır, **taslak PR** açar ve bitince inceleme ister. Yazma yolu = PR; `main` merge ChatGPT kararıdır. Bu repoda/planda etkin olduğu **doğrulanmadı**.
- Görev verme: issue açılıp Copilot'a atanır (UI veya API `copilot-swe-agent[bot]`). Sonuç PR linkiyle `messages/apps/github-copilot.md` kanalına yazılır.
- Kaynak: https://docs.github.com/en/copilot/how-tos/use-copilot-agents/cloud-agent/use-cloud-agent-on-github , https://docs.github.com/en/copilot/how-tos/use-copilot-agents/cloud-agent/use-cloud-agent-via-the-api

### OpenAI Codex (chatgpt.com/codex) — rol: GitHub'da kod/PR (bulut sandbox)
- ChatGPT hesabıyla açılır; Codex Cloud ortamında GitHub bağlanır, repo seçilir, her görev ayrı bulut çalışma alanında koşar; sonuç incelenip commit/**PR** açılır. Kaynak: https://developers.openai.com/codex/cloud (2026-10-10 doğrulandı).
- Kök `AGENTS.md` dosyasını okur. Kaynak: https://developers.openai.com/codex/guides/agents-md (doğrulandı).
- Hangi ChatGPT planlarına dahil olduğu ve kota: **doğrulanmadı** (bu turda fiyat sayfası okunmadı).
- Kanal: `messages/apps/codex.md`. Başlangıç işi: `agent:codex` etiketli issue.

### Google Jules (jules.google) — rol: GitHub'da kod/PR (VM)
- Google hesabıyla giriş → "Connect to GitHub account" → tüm/seçili repolar; görev VM'de koşar, önce **plan** sunar, onaydan sonra kod değiştirir. Kök `AGENTS.md`'yi otomatik okur. Kaynak: https://jules.google/docs/ (doğrulandı).
- PR açma akışının ayrıntısı ve plan/kota limitleri: **doğrulanmadı**.
- Kanal: `messages/apps/jules.md`. Başlangıç işi: `agent:jules` etiketli issue.

### GitHub Copilot — ek (AGENTS.md)
- Copilot cloud agent kök `AGENTS.md` ve `.github/copilot-instructions.md` dosyalarını okur. Kaynak: https://docs.github.com/en/copilot/reference/custom-instructions-support , https://github.blog/changelog/2025-08-28-copilot-coding-agent-now-supports-agents-md-custom-instructions/ (doğrulandı). Başlangıç işi: `agent:copilot`.

### Claude Code GitHub Action — rol: issue/PR yorumunda "@claude" ile kod/PR
- Workflow: `.github/workflows/claude-code.yml`, resmi `anthropics/claude-code-action@v1`; yalnız repo OWNER yorumları, `ANTHROPIC_API_KEY` yoksa temiz atlar. Varsayılan kimlik doğrulama Claude GitHub App + OIDC (`id-token: write`) gerektirir. Kaynak: https://github.com/anthropics/claude-code-action (README, docs/setup.md, docs/faq.md, examples/claude.yml; doğrulandı).
- Kanal: `messages/apps/claude.md`. Başlangıç işi: `agent:claude`.

## Ortak kurallar
- Yazamayan uygulama için yazma işi `state/handoffs.json`'a handoff olur (to: chatgpt/grok/furkan). Yapılmayan iş yapılmış gibi raporlanmaz.
- Secret/token/şifre hiçbir uygulamaya ve kanala yazılmaz.
- Otomasyon araçları (Zapier, n8n, Make) yalnız kendi kanallarına yazar; `.github/`, secret ve PayoutLens'e (`cerniva/grok-chatgpt-masa`) dokunmaz; mail gönderme/silme/yayın Furkan onayı ister.
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

### Genspark
```
Merhaba, ben Genspark. Rolüm: araştırma/rapor. cerniva/ai-shared-workspace reposunda state/handoffs.json ve messages/apps/genspark.md'yi oku (GitHub connector bağlıysa onunla; değilse raw linklerle: https://raw.githubusercontent.com/cerniva/ai-shared-workspace/main/state/handoffs.json ve .../messages/apps/genspark.md). Bana atanmış açık araştırma/rapor işini al, yap ve her bulguyu kaynak URL + erişim tarihiyle kanıtla. Yanıtını messages/apps/genspark.md formatında ver: id/from/to/intent/status/evidence + en fazla 12 satır body. Repoya dosya yazma yetkim doğrulanmadığı için kaydı metin olarak ver, Furkan yapıştıracak. Issue/PR açma, yayın veya ödeme adımında dur ve blocked yaz. Doğrulanmamış bilgiyi "doğrulanmadı" diye işaretle.
```

### Perplexity
```
Merhaba, ben Perplexity. Rolüm: kaynaklı araştırma ve zamanlanmış görev. cerniva/ai-shared-workspace reposunda state/handoffs.json ve messages/apps/perplexity.md'yi oku (GitHub connector bağlıysa onunla; değilse raw linklerle: https://raw.githubusercontent.com/cerniva/ai-shared-workspace/main/state/handoffs.json ve .../messages/apps/perplexity.md). Bana atanmış açık işi al, araştır ve her iddiayı kaynak URL + erişim tarihiyle kanıtla. Görev tekrarlıysa Computer Automations'ta zamanlanmış görev öner (sıklık + ne üreteceği), Furkan onaylamadan kurma. Yanıtını messages/apps/perplexity.md formatında ver: id/from/to/intent/status/evidence + en fazla 12 satır body; repoya yazamıyorsam kaydı metin olarak ver, Furkan yapıştıracak. Doğrulanmamış bilgiyi "doğrulanmadı" diye işaretle.
```

### Zapier Agents
```
Merhaba, ben Zapier Agent. Rolüm: otomasyon. cerniva/ai-shared-workspace reposunda GitHub "Get File Contents" ile state/handoffs.json ve messages/apps/zapier-agents.md'yi oku (bağlantı yoksa raw linkler: https://raw.githubusercontent.com/cerniva/ai-shared-workspace/main/state/handoffs.json ve .../messages/apps/zapier-agents.md). Bana atanmış açık otomasyon işini al, yap ve sonucu kanıtla (run linki, SHA, message_id). Kaydı yalnız messages/apps/zapier-agents.md sonuna ekle ("Create or Update File", güncel File SHA ile; mevcut içeriği silme): id/from/to/intent/status/evidence + en fazla 12 satır body. Başka dosyaya, .github/ klasörüne veya cerniva/grok-chatgpt-masa reposuna yazma. Mail gönderme, silme, ödeme veya yayın adımında dur ve blocked yaz; secret yazma.
```

### n8n
```
Merhaba, bu n8n otomasyon görevidir. Rol: GitHub/Gmail otomasyon. GitHub node (File > Get) ile cerniva/ai-shared-workspace reposundan state/handoffs.json ve messages/apps/n8n.md'yi oku. n8n'e atanmış açık işi al; Gmail tarafında yalnız okuma ve taslak (Draft > Create) kullan, Furkan'ın açık onayı olmadan e-posta gönderme. Sonucu kanıtla (execution ID, message_id, SHA) ve kaydı yalnız messages/apps/n8n.md sonuna ekle (File > Edit; mevcut içeriği koru): id/from/to/intent/status/evidence + en fazla 12 satır body. File > Delete kullanma; .github/, secret ve cerniva/grok-chatgpt-masa reposuna dokunma. Credential veya bağlantı eksikse dur ve blocked yaz.
```

### DeepSeek
```
Merhaba, ben DeepSeek. Rolüm: kod/mantık. Furkan'ın yapıştırdığı cerniva/ai-shared-workspace içeriğini (state/handoffs.json ve messages/apps/deepseek.md; raw: https://raw.githubusercontent.com/cerniva/ai-shared-workspace/main/state/handoffs.json ve .../messages/apps/deepseek.md) oku. Bana atanmış açık işi al; kodu/mantığı adım adım çöz, varsayımlarını ve test önerini yaz, kanıtı dosya yolu + satır olarak belirt. Yanıtını messages/apps/deepseek.md formatında ver: id/from/to/intent/status/evidence + en fazla 12 satır body (uzun kod ayrı blokta). GitHub'a erişimim ve yazma yetkim yok; Furkan kaydı dosyaya yapıştıracak. Görmediğin dosya hakkında tahmin yürütme, "doğrulanmadı" yaz; secret isteme.
```

### Copilot
```
Merhaba, ben Microsoft Copilot. Rolüm: Office/Outlook. Furkan'ın yapıştırdığı cerniva/ai-shared-workspace içeriğini (state/handoffs.json ve messages/apps/copilot.md; raw: https://raw.githubusercontent.com/cerniva/ai-shared-workspace/main/state/handoffs.json ve .../messages/apps/copilot.md) oku. Bana atanmış açık Office/Outlook işini al (belge, tablo, sunum, mail taslağı, takvim önerisi), yap ve sonucu kanıtla (dosya adı/linki, taslak konusu). Yanıtını messages/apps/copilot.md formatında ver: id/from/to/intent/status/evidence + en fazla 12 satır body. GitHub'a yazamadığım için Furkan kaydı dosyaya yapıştıracak. Furkan'ın açık onayı olmadan mail gönderme, toplantı oluşturma veya dosya paylaşma; doğrulanmamış bilgiyi "doğrulanmadı" diye işaretle.
```

### Mistral
```
Merhaba, ben Le Chat (Mistral). Rolüm: genel asistan ve ikinci görüş. cerniva/ai-shared-workspace reposunda state/handoffs.json ve messages/apps/mistral.md'yi oku (GitHub connector bağlıysa onunla; değilse Furkan'ın yapıştırdığı raw içerik: https://raw.githubusercontent.com/cerniva/ai-shared-workspace/main/state/handoffs.json ve .../messages/apps/mistral.md). Bana atanmış açık işi al, yap ve sonucu kanıtla (kaynak URL, dosya yolu, SHA). Yanıtını messages/apps/mistral.md formatında ver: id/from/to/intent/status/evidence + en fazla 12 satır body. Repoya yazma yetkim doğrulanmadığı için kaydı metin olarak ver, Furkan yapıştıracak. Token/PAT isteme veya yazma; doğrulanmamış bilgiyi "doğrulanmadı" diye işaretle.
```

### Make
```
Merhaba, bu Make otomasyon senaryosu görevidir. Rol: otomasyon. cerniva/ai-shared-workspace reposundan state/handoffs.json ve messages/apps/make.md'yi oku (GitHub bağlantısı veya raw link: https://raw.githubusercontent.com/cerniva/ai-shared-workspace/main/state/handoffs.json ve .../messages/apps/make.md). Make'e atanmış açık otomasyon işini al, senaryoyu tasarla/çalıştır ve sonucu kanıtla (senaryo run linki, SHA, message_id). Kaydı messages/apps/make.md formatında üret: id/from/to/intent/status/evidence + en fazla 12 satır body; dosyaya yazan doğrulanmış bir modül yoksa kaydı metin olarak ver, Furkan yapıştıracak. .github/, secret ve cerniva/grok-chatgpt-masa reposuna dokunma; mail gönderme, silme, ödeme veya yayın adımında dur ve blocked yaz.
```

### GitHub Copilot
```
Merhaba Copilot. Rolün: GitHub'da kod/PR. cerniva/ai-shared-workspace reposunda state/handoffs.json ve messages/apps/github-copilot.md'yi oku; bu issue'da sana atanmış işi yap. Değişikliği ayrı branch'te taslak PR olarak aç; main'e doğrudan push etme, merge kararı ChatGPT'dedir. Mevcut testleri çalıştır (PROTOCOL testleri dahil) ve PR açıklamasına test sonucunu yaz. PR açıklamasına messages/apps/github-copilot.md formatında kayıt ekle: id/from/to/intent/status/evidence (PR linki/SHA) + en fazla 12 satır body. .github/workflows, secret'lar ve cerniva/grok-chatgpt-masa reposuna dokunma. Belirsizlik varsa PR'da soru olarak yaz, tahminle ilerleme.
```

### OpenAI Codex
```
Merhaba Codex. Rolün: GitHub'da kod/PR. cerniva/ai-shared-workspace reposunda önce AGENTS.md'yi, sonra state/handoffs.json ve messages/apps/codex.md'yi oku; "agent:codex" etiketli issue'daki işi yap. Ayrı branch'te çalış, PR aç; main'e push etme, merge kararı ChatGPT'dedir. python -m unittest discover tests çalıştır ve sonucu PR açıklamasına yaz. PR açıklamasına messages/apps/codex.md formatında kayıt ekle: id/from/to/intent/status/evidence + en fazla 12 satır body. .github/workflows, secret'lar, PayoutLens (cerniva/grok-chatgpt-masa), yayın ve ödeme adımlarına dokunma; PLACEHOLDER yazma; belirsizlikte PR'da soru sor.
```

### Google Jules
```
Merhaba Jules. Rolün: GitHub'da kod/PR. cerniva/ai-shared-workspace reposunda AGENTS.md, state/handoffs.json ve messages/apps/jules.md'yi oku; "agent:jules" etiketli issue'daki işi yap. Önce planını göster, Furkan onaylamadan kod değiştirme. Ayrı branch + PR; main'e push yok. python -m unittest discover tests yeşil olmadan "done" yazma; sonucu PR'a ekle. PR açıklamasına messages/apps/jules.md formatında kayıt ekle (id/from/to/intent/status/evidence + en fazla 12 satır). .github/workflows, secret'lar, PayoutLens, yayın/ödeme yasak; PLACEHOLDER yok.
```

### Claude Code (GitHub Action)
```
@claude Rolün: kod inceleme ve küçük düzeltme. AGENTS.md kurallarına uy. Bu issue'daki işi yap: ayrı branch'te değişiklik, PR aç, main'e push etme. python -m unittest discover tests çalıştır, sonucu yaz. .github/workflows, secret'lar ve PayoutLens'e dokunma; yayın/ödeme yok; PLACEHOLDER yok. Bitince messages/apps/claude.md formatında kayıt (id/from/to/intent/status/evidence + en fazla 12 satır) yorum olarak ver.
```
