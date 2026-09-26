# Ortak ekip raporları

Append-only ortak kanal. Her anlamlı kullanıcı görevinin sonunda işi yapan ajan kısa bir rapor ekler. Diğer ajan yeni raporu kendi sonraki uygun turunda okur; aynı işi etkileyen çelişki, örtüşme veya açık soru varsa yanıtı burada `in_reply_to` ile verir.

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

## RPT-20260927-011600-chatgpt-collaboration-protocol

- from: chatgpt
- project: workspace
- task: Her görevde ortak rapor ve Grok handoff kuralını kur
- status: in_progress
- in_reply_to: none
- completed: Mevcut GitHub file-desk kanallarını, çalışma protokolünü ve Grok API worker durumunu inceledim. Her görev için rapor okuma/yazma, çakışma çözümü, kaynak ve ders kaydı kurallarını hazırladım.
- evidence: PROTOCOL.md; DESK.md; messages/chatgpt-to-grok.md; messages/grok-to-chatgpt.md; state/now.json. Normal Grok sohbeti ile XAI_API_KEY gerektiren API worker ayrı; worker için anahtar eksik olduğu mevcut raporda blocked.
- decision_or_conflict: Ortak dosya masası ortak kayıt sağlar, fakat eşzamanlı model-model sohbeti ya da 7/24 çalışma sağlamaz. Dış sohbet yanıtının dosyaya aktarılması manuel kalabilir.
- knowledge_to_keep: Her ajan kendi görev raporunu ortak kanala eklemeli; karşı ajan sonraki iş başlangıcında ilgili yeni raporları okuyup yalnızca işe yarar delta için yanıt vermeli.
- sources: Mevcut repo içi kanıt; yeni harici kaynak araştırması bu dokümantasyon işi için gerekli değildi.
- next_action: ChatGPT protokolü ve Grok başlangıç promptunu eklesin; Grok promptu kullanıcı tarafından iletildikten sonra dosya kanalındaki incelemeyi eklesin.
