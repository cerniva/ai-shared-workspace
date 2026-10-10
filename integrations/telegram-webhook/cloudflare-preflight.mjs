// Read-only account check. Never prints response bodies or credential values.
import https from 'node:https';
import { pathToFileURL } from 'node:url';

export function settingsRequest(url, token) {
  return new Promise((resolve, reject) => {
    const request = https.get(url, {headers: {Authorization: 'Bearer ' + token}},
      response => {
        let body = '';
        response.setEncoding('utf8');
        response.on('data', chunk => {
          body += chunk;
          if (body.length > 1024 * 1024) request.destroy(new Error('response limit'));
        });
        response.on('end', () => resolve({status: response.statusCode, body}));
        response.on('error', reject);
      });
    request.setTimeout(15000, () => request.destroy(new Error('timeout')));
    request.on('error', reject);
  });
}

export async function preflight(env, get = settingsRequest) {
  const required = ['CLOUDFLARE_API_TOKEN', 'CLOUDFLARE_ACCOUNT_ID', 'CLOUDFLARE_WORKER_NAME'];
  const missing = required.filter(name => !env[name]);
  if (missing.length) return {status: 'blocked', reason: 'missing_configuration', missing};
  if (!/^[a-f0-9]{32}$/i.test(env.CLOUDFLARE_ACCOUNT_ID) ||
      !/^[a-zA-Z0-9_-]{1,63}$/.test(env.CLOUDFLARE_WORKER_NAME) ||
      /[\r\n]/.test(env.CLOUDFLARE_API_TOKEN))
    return {status: 'blocked', reason: 'invalid_configuration'};
  const url = 'https://api.cloudflare.com/client/v4/accounts/' +
    env.CLOUDFLARE_ACCOUNT_ID + '/workers/scripts/' + env.CLOUDFLARE_WORKER_NAME + '/settings';
  let response;
  try { response = await get(url, env.CLOUDFLARE_API_TOKEN); }
  catch { return {status: 'blocked', reason: 'network_error'}; }
  if (response.status !== 200)
    return {status: 'blocked', reason: 'cloudflare_http_error', http_status: response.status};
  let data;
  try { data = JSON.parse(response.body); }
  catch { return {status: 'blocked', reason: 'invalid_response'}; }
  if (data?.success !== true || !Array.isArray(data.result?.bindings))
    return {status: 'blocked', reason: 'invalid_response'};
  const names = ['TELEGRAM_BOT_TOKEN', 'TELEGRAM_ALLOWED_CHAT_ID', 'TELEGRAM_WEBHOOK_SECRET'];
  const bindings = Object.fromEntries(names.map(name => {
    const binding = data.result.bindings.find(item => item?.name === name);
    return [name, binding?.type === 'secret_text' ? 'secret_present' :
      binding ? 'not_secret' : 'missing'];
  }));
  return {status: 'read_access_verified', bindings,
    deployment_verified: false, webhook_changed: false};
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const result = await preflight(process.env);
  console.log(JSON.stringify(result));
  if (result.status !== 'read_access_verified') process.exitCode = 1;
}
