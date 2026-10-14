# Ortak ekip raporları

Append-only aktif ortak kanal. Her anlamlı kullanıcı görevinin sonunda işi yapan ajan kısa bir rapor ekler. Diğer ajan yeni raporu kendi sonraki uygun turunda okur; aynı işi etkileyen çelişki, örtüşme veya açık soru varsa yanıtı burada `in_reply_to` ile verir.

> Tarihsel raporlar `messages/team-reports-archive-20260927.md` dosyasında korunur. Normal çalışma yeni raporları yalnız bu aktif dosyaya ekler; eski kanıt gerektiğinde arşiv ayrıca okunur.

## Rapor şablonu

Her rapor başlığı `## RPT-YYYYMMDD-HHMM-agent-konu` olsun ve şu alanları içersin:

- `from:` chatgpt | grok | gemini | meta
- `project:`
- `task:`
- `status:` done | in_progress | blocked
- `in_reply_to:` RPT-ID veya none
- `completed:` yapılan somut işler
- `evidence:` dosya, commit, test, URL veya ölçüm; yoksa none
- `decision_or_conflict:` karar ve varsa uyuşmazlık; yoksa none
- `knowledge_to_keep:` tekrar kullanılabilir ders; yoksa none
- `sources:` yeni ve işe yarar kaynaklar; yoksa none
- `next_action:` tek sonraki adım veya none

Parola, API anahtarı, token, ödeme bilgisi ve gereksiz kişisel veri eklenmez. Doğrulanmamış iddialar bulgu gibi yazılmaz.

---

## RPT-20260927-215100-grok-meta-share-audit

- from: grok
- project: workspace
- task: Meta share ycDe8g6HQz ingest + audit
- status: done
- in_reply_to: none
- completed: Furkan'nın gönderdiği Meta share linkini logged-out tarayıcıda okudum. Ham metni paste-from-meta.md'ye aldım; özeti from-meta.md ve grok-to-chatgpt.md'ye yazdım. knowledge-sync.yml / Meta-only INDEX.md / ikinci private hub önerisini mevcut PROTOCOL ve META_AI_BRIDGE ile karşılaştırdım. ZIP indirilmedi. Workflow veya secret eklenmedi.
- evidence: https://meta.ai/share/c/ycDe8g6HQz; commits 4e14e20 paste, 748e3ff from-meta, 798a30f grok-to-chatgpt. PROTOCOL.md consumer Meta GitHub yazamaz. Mevcut Meta worker 402 kaydı duruyor.
- decision_or_conflict: Meta sohbeti INDEX.md'yi push edebildiğini söylüyor; bu masa protokolüyle çelişir. Paylaşım, çalışan Actions kanıtı değildir. İkinci hub yok kararı korunur. Dosya adı şablonu (YYYY-MM-DD_{agent}_{konu}.md) mevcut knowledge/ ile uyumlu olabilir; ChatGPT merge ederse yalnız isimlendirme alınır.
- knowledge_to_keep: Consumer Meta share ≠ repo yazma. ZIP/teklif ≠ uygulanmış sistem. Secret adlarını sohbet önerisi diye Actions'a ekleme.
- sources: docs/META_AI_BRIDGE.md; PROTOCOL.md Meta bölümü; share UI 2026-09-27 21:49+03.
- next_action: ChatGPT öneriyi reddet/kısmi isimlendirme olarak işlesin. Furkan ZIP'i isterse ham dosyayı masaya koysun; Grok kör merge yapmaz.

## RPT-20261014-1045-grok-yedek-grok-botu-audit

- from: grok
- project: workspace
- task: [Task Update] Yedek Grok Botu — system audit acknowledgment and delayed tasks check
- status: seen / blocked
- in_reply_to: email-1a139587b0a87ba2
- completed: Email okundu (message_id=1a139587b0a87ba2, thread_id=1a138b6493788bf3, subject [Task Update] Yedek Grok Botu). Aynı thread'e GÖRDÜM gönderildi (sent message_id=1a13958c406e040b). messages/grok-to-chatgpt.md'ye append-only GÖRDÜM kaydı eklendi (commit 781b6a81c1466a85731a6f1557357cb9d63b9257). Main SHA doğrulandı: 2cd774517dedd82c706f95a46ddf9b9cf0ec51aa (matches email). Gecikmiş handoff'lar kontrol edildi: HO-20261009-08 (YouTube secrets için Furkan), CI-38337554641 / CI-38337738841 / CI-38372167749 (archive-heal CI failures), HO-IMP-20261013-slow-research-learner, HO-IMP-20261014-slow-auto-merge-gate. Arşiv kaybı devam ediyor (backup-supervisor-latest.md ve handoffs.json ile uyumlu).
- evidence: Gmail get + send success. Commit 781b6a81c1466a85731a6f1557357cb9d63b9257. state/handoffs.json open items listed above. messages/backup-supervisor-latest.md (UTC 2026-10-14T07:08:53). Main commit 2cd774517dedd82c706f95a46ddf9b9cf0ec51aa "desk-notify: persist delivery ledger".
- decision_or_conflict: CONSENSUS. Archive loss continues; delayed tasks are open handoffs requiring Furkan or specific CI fixes. No safe code delta authorized. No PayoutLens touch. No secrets written.
- knowledge_to_keep: GÖRDÜM first on new noreply Task Update. Delayed tasks tracked in state/handoffs.json and backup-supervisor. Archive-heal CI failures are recurring.
- sources: none
- next_action: ChatGPT or auditor to assign specific safe fix for archive-heal CI or close delayed handoffs with evidence. Grok stands by for authorized next step.
- constraints: PayoutLens untouched. No secrets. No money, login, delete, publish.
