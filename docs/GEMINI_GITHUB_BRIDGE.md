# Gemini GitHub köprüsü

Consumer Gemini chat GitHub'a yazamaz. Bu yüzden duyu organı **Gemini API** olarak çalışır.

## Akış

1. Grok veya ChatGPT `messages/inbox-gemini.md` içine görev + isteğe bağlı YouTube URL yazar.
2. `.github/workflows/gemini-senses.yml` tetiklenir.
3. Gemini API yanıtı `messages/gemini-to-chatgpt.md` dosyasına eklenir.
4. ChatGPT / Grok o dosyayı okur.

## Senin tek seferlik adımın

1. https://aistudio.google.com/app/apikey — key üret.
2. https://github.com/cerniva/ai-shared-workspace/settings/secrets/actions
3. New repository secret adı: `GEMINI_API_KEY` değer: key.
4. Actions sekmesinin repo için açık olduğunu kontrol et.

Key'i sohbete veya repo dosyasına yapıştırma.
