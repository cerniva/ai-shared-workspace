import assert from 'node:assert/strict';
import { test } from 'node:test';
import worker from './worker.mjs';

const env = { TELEGRAM_BOT_TOKEN: 'fake-test-token', TELEGRAM_ALLOWED_CHAT_ID: '123', TELEGRAM_WEBHOOK_SECRET: 'test-secret' };
const originalFetch = globalThis.fetch;
const request = (method='POST', body={}, secret='test-secret') => new Request('https://example.invalid/webhook', {method, headers: {'X-Telegram-Bot-Api-Secret-Token':secret}, ...(method==='POST'?{body:typeof body==='string'?body:JSON.stringify(body)}:{})});
const update = (text,chat=123)=>({update_id:1,message:{chat:{id:chat},text}});
test('rejects GET',async()=>assert.equal((await worker.fetch(request('GET'),env)).status,404));
test('rejects missing secrets',async()=>assert.equal((await worker.fetch(request('POST'),{})).status,503));
test('rejects wrong secret',async()=>assert.equal((await worker.fetch(request('POST',{},'wrong'),env)).status,403));
test('rejects malformed JSON',async()=>assert.equal((await worker.fetch(request('POST','{'),env)).status,400));
test('ignores unauthorized chat',async()=>assert.equal((await worker.fetch(request('POST',update('/start',999)),env)).status,200));
test('ignores noncommands without network call',async()=>{globalThis.fetch=()=>{throw Error('unexpected network')};try{assert.equal((await worker.fetch(request('POST',update('hello')),env)).status,200)}finally{globalThis.fetch=originalFetch}});
test('sends authorized command',async()=>{let sent;globalThis.fetch=async(url,opts)=>{sent=JSON.parse(opts.body);return new Response('{}',{status:200})};try{assert.equal((await worker.fetch(request('POST',update('/start')),env)).status,200);assert.equal(sent.chat_id,123)}finally{globalThis.fetch=originalFetch}});
test('handles Telegram HTTP failure',async()=>{globalThis.fetch=async()=>new Response('failed',{status:500});try{assert.equal((await worker.fetch(request('POST',update('/durum')),env)).status,502)}finally{globalThis.fetch=originalFetch}});
test('handles Telegram network failure',async()=>{globalThis.fetch=async()=>{throw Error('network down')};try{assert.equal((await worker.fetch(request('POST',update('/durum')),env)).status,502)}finally{globalThis.fetch=originalFetch}});
