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

## RPT-20260928-1641-chatgpt-shorts-core05-fixes

- from: chatgpt
- project: workspace/content
- task: CORE-05 sorun giderme + zero-credit Shorts hattını güvenli hale getirme
- status: done
- in_reply_to: none
- completed: PR #34 içindeki iki CodeRabbit doğruluk bulgusu giderildi: gizli `.mp4` artifact adı reddediliyor ve sentezlenmiş anlatım hedef süreden uzunsa render fail-closed duruyor. Regresyon testleri eklendi; PR #34 main'e squash merge edildi. PR #36 CORE-05 knowledge adapter docstring düzeltmesi CI/CodeQL sonrası merge edildi. `state/now.json` gerçek planner sırasıyla Gemini→OpenAI→Grok→Anthropic olarak senkronlandı.
- evidence: main commits 94488d0903dbf013d7e549cc2eb9cfc395a847ab, 24315a84141e49701217b4b51dd0ae3fc8d79d7b; PR #34 review threads resolved; post-merge shorts-render-tests success; worker-orchestration-tests success; CodeQL Python+JS/TS success; browser_worker/ai_planner.py current `_providers()` order.
- decision_or_conflict: Ücretsiz render hattı artık main'de ve doğrulanmış durumda; ancak render artifact üretimi YouTube yayını değildir. Mevcut `.github/workflows/youtube-upload.yml` repo-relative MP4 beklediği için render artifact → uploader aktarımı hâlâ ayrı bir entegrasyon açığıdır.
- knowledge_to_keep: TTS ses sinyalinin bulunması tek başına yeterli değildir; anlatım süresi ayrıca hedef video süresine karşı doğrulanmalıdır. Artifact isimleri upload-artifact hidden-file davranışıyla uyumlu olmalıdır.
- sources: repository CI/review evidence only; no new external source.
- next_action: zero-credit render artifact'ını YouTube uploader'a güvenli ve varsayılanı private/fail-closed olacak şekilde aktaracak köprüyü ekle; OAuth upload secret yoksa yayın yapma ve eksik secretı açıkça blocker olarak raporla.
