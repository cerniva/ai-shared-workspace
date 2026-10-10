import assert from 'node:assert/strict';
import {test} from 'node:test';
import {preflight} from './cloudflare-preflight.mjs';
const env = {CLOUDFLARE_API_TOKEN:'local-test-credential', CLOUDFLARE_ACCOUNT_ID:'a'.repeat(32), CLOUDFLARE_WORKER_NAME:'existing-worker'};
test('missing config makes no request', async () => {
  const result = await preflight({}, () => {throw Error('unexpected request')});
  assert.equal(result.reason, 'missing_configuration');
});
test('rejects path injection and credential newlines', async () => {
  for (const change of [{CLOUDFLARE_WORKER_NAME:'../other'}, {CLOUDFLARE_ACCOUNT_ID:'bad'}, {CLOUDFLARE_API_TOKEN:'bad\nvalue'}])
    assert.equal((await preflight({...env,...change})).reason,'invalid_configuration');
});
test('classifies bindings without printing values', async () => {
  const result = await preflight(env, async (url, token) => {
    assert.match(url,/^https:\/\/api\.cloudflare\.com\/client\/v4\/accounts\//);
    assert.equal(token,env.CLOUDFLARE_API_TOKEN);
    return {status:200, body:JSON.stringify({success:true,result:{bindings:[
      {name:'TELEGRAM_BOT_TOKEN',type:'secret_text',text:'sensitive-value'},
      {name:'TELEGRAM_ALLOWED_CHAT_ID',type:'plain_text',text:'private-id'}
    ]}})};
  });
  assert.equal(result.status,'read_access_verified');
  assert.deepEqual(Object.values(result.bindings),['secret_present','not_secret','missing']);
  assert.equal(result.webhook_changed,false);
  assert.doesNotMatch(JSON.stringify(result),/sensitive-value|private-id|local-test-credential/);
});
test('HTTP failures and redirects never expose bodies', async () => {
  for (const status of [301,401,403,404,500]) {
    const result = await preflight(env,async()=>({status,body:'sensitive-value'}));
    assert.equal(result.http_status,status);
    assert.doesNotMatch(JSON.stringify(result),/sensitive-value/);
  }
});
test('network errors are redacted', async () => {
  const result=await preflight(env,async()=>{throw Error('sensitive-value')});
  assert.deepEqual(result,{status:'blocked',reason:'network_error'});
});
test('rejects malformed API responses',async()=>{
  for(const body of ['bad', 'null', '{"success":false}', '{"success":true,"result":{}}'])
    assert.equal((await preflight(env,async()=>({status:200,body}))).reason,'invalid_response');
});
