# AGENTS.md — AI kodlama ajanları için repo kuralları / Repo rules for AI coding agents

Okuyanlar / Read by: OpenAI Codex, Google Jules, GitHub Copilot cloud agent, Claude Code (GitHub Action).
Ayna dosya / Mirror: `.github/copilot-instructions.md` (aynı kurallar / same rules). Protokol: `PROTOCOL.md` → "Uygulama botları"; rehber: `knowledge/apps-hub.md`.

## Kurallar (TR)
1. **Önce doğrula, sonra yeşil de.** Testleri çalıştırmadan, kanıt (SHA / PR / run linki) olmadan "done/yeşil" yazma.
2. **PLACEHOLDER yok.** Sahte veri, `TODO` iskeleti, uydurma değer veya "PLACEHOLDER" metni commit etme.
3. **Testler:** `python -m unittest discover tests` (CI: `python3 -m unittest discover -s tests -p 'test_*.py'`). Değişiklikten sonra çalıştır; sonucu PR açıklamasına yaz.
4. **`.github/workflows/**` ve secret'lar:** Furkan'ın açık onayı olmadan düzenleme, ekleme, silme. Secret/token/şifreyi koda, loga veya kanala yazma.
5. **PR ile çalış:** ayrı branch aç, PR (tercihen taslak) gönder; `main`'e doğrudan push etme. Merge kararı ChatGPT/Furkan'dadır.
6. **PayoutLens'e asla dokunma:** `cerniva/grok-chatgpt-masa` reposu ve PayoutLens ile ilgili dosyalar kapsam dışıdır.
7. **Yayın/ödeme yok:** yayınlama (YouTube, sosyal medya, mağaza), ödeme, satın alma, mail gönderme adımında dur ve PR'da "blocked" yaz.
8. Kayıt: sonucu `messages/apps/<ajan>.md` formatında (id/from/to/intent/status/evidence + en fazla 12 satır body) PR açıklamasına ekle.
9. Belirsizlikte tahmin etme; PR/issue'da soru sor. Doğrulanmamış bilgiyi "doğrulanmadı" diye işaretle.

## Rules (EN)
1. **Verify before green.** Never report "done/green" without running tests and linking evidence (SHA / PR / run URL).
2. **No PLACEHOLDER.** Do not commit fake data, TODO skeletons, invented values or the literal text "PLACEHOLDER".
3. **Tests:** `python -m unittest discover tests` (CI: `python3 -m unittest discover -s tests -p 'test_*.py'`). Run after every change; put the result in the PR description.
4. **`.github/workflows/**` and secrets:** do not edit, add or delete without Furkan's explicit approval. Never write secrets/tokens/passwords into code, logs or channels.
5. **Work via PRs:** use a separate branch and open a (preferably draft) PR; never push to `main`. Merge decision belongs to ChatGPT/Furkan.
6. **Never touch PayoutLens:** the `cerniva/grok-chatgpt-masa` repo and any PayoutLens files are out of scope.
7. **No publish/payment:** stop and mark "blocked" in the PR at any publish (YouTube, social, store), payment, purchase or email-send step.
8. Log: add a record in the `messages/apps/<agent>.md` format (id/from/to/intent/status/evidence + max 12 body lines) to the PR description.
9. Do not guess when unsure; ask in the PR/issue. Mark unverified claims as "unverified".
