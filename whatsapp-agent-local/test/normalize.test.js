import test from 'node:test';
import assert from 'node:assert/strict';
import { normalizeInbound } from '../src/normalize.js';

test('normalize expone chatJid y conversation_id', () => {
  const msg = normalizeInbound({
    chatJid: '56912345678@s.whatsapp.net',
    msgId: 'ABC123',
    sender: '56912345678@s.whatsapp.net',
    pushName: 'Erwin',
    text: 'Hola',
    timestamp: 1759000000,
  });

  assert.equal(msg.chat_jid, '56912345678@s.whatsapp.net');
  assert.equal(msg.chatJid, '56912345678@s.whatsapp.net');
  assert.equal(msg.conversation_id, 'wa:56912345678');
  assert.equal(msg.sender_id, '56912345678');
  assert.equal(msg.type, 'text');
  assert.equal(msg.text, 'Hola');
  assert.equal(msg.metadata.chat_jid, '56912345678@s.whatsapp.net');
  assert.ok(msg.timestamp);
});

test('normalize marca mensajes sin texto como unsupported', () => {
  const msg = normalizeInbound({
    chatJid: '56911111111@s.whatsapp.net',
    msgId: 'X',
    sender: '56911111111@s.whatsapp.net',
    pushName: '',
    text: '',
    timestamp: undefined,
  });
  assert.equal(msg.type, 'unsupported');
  assert.equal(msg.text, '');
});

test('normalize maneja jid de grupo con participante', () => {
  const msg = normalizeInbound({
    chatJid: '120363000000000000@g.us',
    msgId: 'G1',
    sender: '56922222222@s.whatsapp.net',
    pushName: '',
    text: 'ping',
    timestamp: 1,
  });
  assert.equal(msg.metadata.is_group, true);
  assert.equal(msg.conversation_id, 'wa:56922222222');
});
