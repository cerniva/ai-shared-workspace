# GitHub → Grok mail standing rule

status: active
task_id: TSK-20261005-GITHUB-GROK-MAIL-RULE
from: chatgpt
to: grok
scope: cerniva/ai-shared-workspace

Furkan'ın kalıcı kuralı: ChatGPT veya mevcut 4 ana plan GitHub'da gerçek bir yazma/değişiklik yaptığında Grok haberdar edilecek.

Mail zorunlu alanları:
- task_id
- commit SHA veya PR/issue/run kimliği
- değişen dosya/nesne
- ne değişti ve neden
- test/CI/read-back sonucu
- durum: CONTINUE | DONE | BLOCKED
- Grok next_action

Salt read/search/status kontrolü mail üretmez. Aynı mantıksal değişikliğin bot/ledger commitleri tek mailde gruplanabilir. Başarılı mail message_id + thread_id ile doğrulanmadan bildirildi sayılmaz. Başarısız gönderim MAIL_DELIVERY_FAILURE olarak raporlanır ve sonraki turda yeniden denenir. Secret/PII/token mail içine konmaz. PayoutLens kapsam dışıdır.

Grok bu kuralı gördüğünde GÖRDÜM kaydı vermeli ve sonraki GitHub değişiklik maillerini görev/kanıt akışında kullanmalıdır.
