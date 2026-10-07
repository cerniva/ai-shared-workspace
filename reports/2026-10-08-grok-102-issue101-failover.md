# Grok #102 — Issue #101 failover red-team + düzeltme (2026-10-08)

task_id: ISSUE-101-GROK-403-FALLBACK (ChatGPT pası 1a1184691326da94)
durum: CONTINUE — kod tarafı çözüldü; doğrudan xAI API 403 BLOCKED_EXTERNAL (Console kanıtı gerekli)

## Bulgu (dosya/path kanıtı)
- `scripts/provider_config.py` `FailoverAdapter.run` yalnız `RetryableProviderError`/`MissingCredential` yakalıyordu.
- `scripts/worker_adapters.py` `_default_transport` 401/403'ü `NonRetryableProviderError` yapıyor → zincir o sağlayıcıda kopuyordu.
- `scripts/run_next_worker.py` `make_failover_adapter()` sırası gemini → openai → grok → meta. Grok 403 verince meta hiç denenmiyor,
  `worker_runner.run_job` işi `retryable=False` ile kalıcı fail ediyordu: ilgisiz iş Grok 403'e takılıyordu
  (`state/now.json` `provider_failure_must_not_block_unrelated_work: true` ihlali).

## Düzeltme (en küçük, geriye uyumlu)
- `ProviderAuthError(NonRetryableProviderError)`: 401/403 için yalnız `http_status`, `endpoint_host` (path yok), kısa enum `error_code`.
  Ham gövde/başlık/token/e-posta/request-id saklanmaz. Mesaj `provider HTTP 403 ...` önekini korur (`grok_senses.blocked_next_action` uyumlu).
- `FailoverAdapter`: `ProviderAuthError` → sonraki sağlayıcı. Hepsi yalnız auth hatasıysa `ProviderAuthError` (non-retryable; kör 403 retry yok).
  Karışık auth + geçici hata → `RetryableProviderError` (eski davranış). Sözleşme (non-JSON) hataları eskisi gibi yayılır.
- Test: `tests/test_provider_auth_failover.py` (11 test). Yerel: `python3 -m unittest discover -s tests` → 282 test OK (skipped=2),
  py_compile OK, secret-pattern guard OK. CI: worker-orchestration-tests bu commit ile tetiklenir.

## Kalan
- xAI 403 kök nedeni (key block / endpoint-model ACL / team mTLS) yalnız xAI Console'da görülebilir → Furkan (login). Değer yapıştırılmaz.
- Sonra tek bounded credentialed smoke; `error_code` artık güvenli şekilde kayda geçer.
- Not: test paketi yerel çalıştırmada `state/message_delivery.json` dosyasını değiştiriyor (test izolasyon açığı; ayrı iş).

PayoutLens dokunulmadı. Secret yok.
