// Cloudflare Worker: restricted Telegram webhook, no paid provider calls.
export default {
  async fetch(request, env) {
    if (request.method !== 'POST') return new Response('Not found', { status: 404 });
    if (!env.TELEGRAM_BOT_TOKEN || !env.TELEGRAM_ALLOWED_CHAT_ID || !env.TELEGRAM_WEBHOOK_SECRET)
      return new Response('Not configured', { status: 503 });
    if (request.headers.get('X-Telegram-Bot-Api-Secret-Token') !== env.TELEGRAM_WEBHOOK_SECRET)
      return new Response('Forbidden', { status: 403 });
    let update;
    try { update = await request.json(); } catch { return new Response('Bad JSON', { status: 400 }); }
    const message = update?.message;
    if (!message || String(message.chat?.id) !== String(env.TELEGRAM_ALLOWED_CHAT_ID))
      return new Response('OK');
    const command = String(message.text || '').trim().split(/\s+/)[0].split('@')[0].toLowerCase();
    if (!command.startsWith('/')) return new Response('OK');
    const replies = {
      '/start': 'Bot aktif. /yardim ile komutları görebilirsin.',
      '/yardim': 'Komutlar: /start, /yardim, /durum. Diğer komutlar henüz bu hızlı kanalda etkin değil.',
      '/durum': 'Telegram webhook bağlantısı aktif. GitHub iş akışlarının durumu bu yanıtla doğrulanmaz.'
    };
    const reply = replies[command] || 'Bu komut hızlı kanalda henüz desteklenmiyor. /yardim yaz.';
    let response;
    try {
      response = await fetch('https://api.telegram.org/bot' + env.TELEGRAM_BOT_TOKEN + '/sendMessage', {
        method: 'POST', headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ chat_id: message.chat.id, text: reply })
      });
    } catch { return new Response('Telegram send failed', { status: 502 }); }
    if (!response.ok) return new Response('Telegram send failed', { status: 502 });
    return new Response('OK');
  }
};
