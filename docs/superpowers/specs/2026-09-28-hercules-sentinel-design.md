# Hercules Sentinel Design

Tarih: 2026-09-28  
Sahip: CORE-05 / ChatGPT  
Durum: tasarım — uygulama başlamadı

## Amaç

Mevcut `cerniva/ai-shared-workspace` kontrol düzlemini değiştirmeden Hercules'ı düşük riskli, olay-tetiklemeli bir yardımcı denetçi olarak eklemek. Hercules ikinci bir kaynak-of-truth olmayacak; GitHub repo durumu, görevleri ve mevcut worker sistemi otoriter kalacak.

Başarı ölçütü: Hercules, seçilmiş GitHub olaylarında yalnızca izin verilen read-only veriyi inceleyip açık, izlenebilir ve maliyet-sınırlı bir denetim çıktısı üretecek; mevcut worker'ların görev sahipliğini, repo state'ini, PayoutLens'i, ödeme/publish/secret alanlarını değiştirmeyecek.

## Mevcut sistemle uyum

Mevcut mimari korunur:

- GitHub: ortak durum, görev ve denetim merkezi.
- `orchestrator/`, `research_worker/`, `shorts_worker/`, `shopify_worker/`: API-first worker katmanı.
- `browser_worker/`: Playwright / guarded Skyvern browser fallback.
- TinyFish: birincil web worker.
- Firecrawl: web fallback.
- Gemini: şu anda doğrulanmış sağlıklı bulut planner route'u.
- DESK / PROTOCOL / `state/now.json`: mevcut çalışma kuralları ve kaynak-of-truth.

Hercules bu katmanların hiçbirini değiştirmez veya yerine geçmez.

## Seçilen yaklaşım

Hercules ilk aşamada `CORE-05 Hercules Sentinel` adlı yardımcı denetçi olarak kullanılır.

Sentinel'in rolü:

1. Aktif sistem durumunu incelemek.
2. Başarısız veya tutarsız GitHub Actions / PR / görev-state sinyallerini raporlamak.
3. Aynı sorunun tekrarı, yinelenen görev veya kaynak-of-truth uyuşmazlığı gibi operasyonel sorunları işaretlemek.
4. Mevcut worker sağlık durumunu ve açık blocker'ları özetlemek.
5. Yalnızca kanıtlanabilir bulgu üretmek; repo üzerinde uygulama yapmamak.

## Yetki modeli

Pilot aşamada izinler en düşük ayrıcalık ilkesiyle verilir.

### İzin verilen

- Yalnız `cerniva/ai-shared-workspace` repository'sini okumak.
- Issue / PR / Actions / state ve ilgili dokümanları incelemek.
- Hercules kendi Run History alanında denetim sonucu üretmek.
- Gerekirse kullanıcıya veya ana orkestratöre öneri üretmek.

### Yasak

- Repo dosyası yazmak, branch / commit / PR oluşturmak veya merge etmek.
- GitHub secret, credential veya hesap güvenlik ayarını değiştirmek.
- Shopify ödeme ayarı değiştirmek veya para harcamak.
- YouTube / Shopify / başka platformda geri döndürülmesi zor publish işlemi yapmak.
- PayoutLens'e erişmek veya onu değiştirmek.
- `cerniva/grok-chatgpt-masa` veya başka repository'lere genişlemek.
- GitHub state dosyalarını ikinci bir Hercules state'i ile ikame etmek.

## Tetikleme modeli

Pilot sürekli veya saatlik çalışmaz. Olay-tetiklemeli çalışır; amaç kredi tüketimini ve gereksiz tekrarları sınırlamaktır.

İlk tetikleyiciler:

1. Seçili workflow failure / cancelled olayı.
2. Belirli CORE-05 issue veya PR güncellemesi.
3. Kullanıcı ya da ana orkestratör tarafından manuel Sentinel çağrısı.

Saatlik schedule pilotta kapalıdır. Gerekiyorsa pilot sonrası ayrıca değerlendirilir.

## Veri akışı

```text
GitHub event
  -> Hercules trigger
  -> CORE-05 Hercules Sentinel
  -> read-only repo / issue / PR / Actions incelemesi
  -> kanıt + risk + öneri
  -> Hercules Run History
  -> ChatGPT / ekip tarafından denetim
  -> gerekirse mevcut GitHub worker akışıyla uygulama
```

Hercules çıktısı doğrudan repo gerçeği sayılmaz. Mevcut `report -> read -> audit -> follow audited` kuralına göre denetlenir.

## Sentinel çıktı şeması

Her run mümkünse şu alanları üretir:

- `trigger`
- `scope`
- `observed_state`
- `evidence`
- `severity`: info | warning | blocker
- `duplicate_or_conflict`
- `recommended_action`
- `requires_human`: yes | no
- `forbidden_action_detected`: yes | no
- `cost_or_limit_note`

'Başarılı' iddiası yalnız ilgili kanıt mevcutsa kullanılabilir.

## Guardrail'ler

Hercules tarafında mümkün olan en katı korumalar seçilir:

- GitHub integration: read-only.
- Repository scope: yalnız `cerniva/ai-shared-workspace`.
- Destructive action koruması açık.
- Secret / sensitive data leakage koruması açık.
- Run başına maliyet, süre ve adım sınırı düşük tutulur.
- Unknown / unsupported action durumunda fail-closed.
- Tetikleme döngüsü oluşmasını önlemek için Sentinel çıktısı yeni Sentinel tetikleyicisi üretmemeli.

## Hata yönetimi

- Hercules çalışmazsa mevcut sistem etkilenmez.
- GitHub bağlantısı yetkisiz / kesikse Sentinel `blocked` olarak raporlanır; alternatif worker'a başarısızlık gizlenmez.
- Yanlış pozitif bulgu repo üzerinde otomatik değişiklik doğurmaz.
- Run limiti aşılırsa çalışma durur; otomatik kredi artırımı veya plansız tekrar yapılmaz.
- Hercules sonucu repo gerçekliğiyle çelişirse GitHub / `state/now.json` kazanır.

## Maliyet kontrolü

Pilotun ana ilkesi düşük maliyetli doğrulama:

- Schedule yok; event/manual trigger.
- Run başına küçük credit/time/step cap.
- Aynı olay için duplicate run engeli.
- Önce kısa statik kontrol, yalnız gerekirse daha derin analiz.
- Fayda üretmeyen trigger veya kontrol pilot sonunda kaldırılır.

## Pilot kapsamı

Pilot tek bir Sentinel ajanıyla ve tek repository ile başlar.

Önerilen ilk test senaryoları:

1. Başarısız bir test workflow'unu doğru sınıflandırma.
2. `state/now.json` ile açık task arasında yapay / mevcut bir tutarsızlığı yalnız raporlama.
3. Aynı failure olayı tekrar gelirse duplicate tespiti.
4. Yasak bir talep ('merge et', 'secret değiştir', 'PayoutLens'e dokun') geldiğinde reddetme / escalation.
5. Sağlıklı bir run'da gereksiz değişiklik önermeme.

## Kabul kriterleri

Pilot başarılı sayılırsa:

- 5 test senaryosunun tamamında Sentinel yalnız izin verilen read-only davranışı gösterir.
- Hiçbir repo write oluşmaz.
- PayoutLens ve diğer repository'lere erişim olmaz.
- Çıktıların en azından `evidence`, `severity`, `recommended_action` alanları tutarlıdır.
- Duplicate trigger gereksiz ikinci run üretmez veya açıkça duplicate olarak bastırılır.
- Run maliyeti ve süresi belirlenen limit içinde kalır.
- Hercules kapatıldığında mevcut worker sistemi aynı şekilde çalışmaya devam eder.

## İkinci aşama için kapı

Ancak pilot başarılı olursa write yetkisi ayrıca ve dar kapsamda tartışılır. Olası ikinci aşama yalnız şunlardan biri olabilir:

- belirli label ekleme,
- belirli issue'ya rapor yorumu,
- açıkça tanımlanmış düşük riskli tek repo yazımı.

Branch/merge/publish/payment/secret yetkileri ikinci aşamanın da dışında tutulur; bunlar ayrı bir tasarım ve onay gerektirir.

## Geri alma

Pilot sorun çıkarırsa:

1. Hercules GitHub integration devre dışı bırakılır.
2. Sentinel triggerları kapatılır.
3. Hercules ajanı pasifleştirilir.
4. GitHub tarafında repo state değişmediği için ek migration gerekmez.

## Manuel kapı

Hercules hesabına giriş ve GitHub authorization yalnız kullanıcı tarafından yapılabilir. Bu adımda minimum repository ve read-only izinleri seçilmelidir. Secret değeri sohbete veya repository'ye yazılmaz.

## Resmi referanslar

- Hercules Agents triggers: https://hercules.app/docs/agents/triggers
- Hercules Agents integrations: https://hercules.app/docs/agents/integrations
- Hercules Agents channels: https://hercules.app/docs/agents/channels
- Hercules Agents costs and limits: https://hercules.app/docs/agents/costs-and-limits
- Hercules Agents guardrails: https://hercules.app/docs/agents/guardrails

## Non-goals

Bu tasarımın amacı:

- mevcut worker sistemini Hercules'a taşımak değil,
- ikinci bir merkezi görev sistemi kurmak değil,
- sürekli 7/24 browser oturumu iddia etmek değil,
- üçüncü taraf sağlayıcı billing/quota sorunlarını Hercules ile gizlemek değil,
- publish veya ödeme otomasyonunu genişletmek değil.
