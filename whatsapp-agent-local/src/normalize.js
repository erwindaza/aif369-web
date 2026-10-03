const numberFromJid = (jid) => String(jid || '').split('@')[0].split(':')[0];

export function normalizeInbound(raw) {
  const { chatJid, msgId, sender, pushName, text, timestamp } = raw;
  const senderId = numberFromJid(sender || chatJid);
  return {
    channel: 'whatsapp',
    message_id: msgId,
    conversation_id: `wa:${senderId}`,
    sender_id: senderId,
    chat_jid: chatJid,
    chatJid: chatJid,
    type: text ? 'text' : 'unsupported',
    text: text || '',
    timestamp: new Date((timestamp || Date.now() / 1000) * 1000).toISOString(),
    metadata: {
      chat_jid: chatJid,
      push_name: pushName || '',
      is_group: typeof chatJid === 'string' && chatJid.endsWith('@g.us'),
    },
  };
}

export const maskSender = (senderId) => `***${String(senderId || '').slice(-4)}`;
