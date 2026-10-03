import { mkdir, rm } from 'node:fs/promises';
import path from 'node:path';
import makeWASocket, {
  DisconnectReason,
  fetchLatestBaileysVersion,
  useMultiFileAuthState,
} from '@whiskeysockets/baileys';
import pino from 'pino';
import qrcode from 'qrcode-terminal';
import QRCode from 'qrcode';
import { authDir, config } from './config.js';
import { markInbound, States, setState } from './state.js';
import { normalizeInbound, maskSender } from './normalize.js';

const logger = pino({ level: 'silent' });
const runtimeDir = path.resolve(config.dataDir, '..', 'runtime');
const qrPngPath = path.join(runtimeDir, 'whatsapp-qr.png');

export const wa = { socket: null, me: null };

const extractText = (message) =>
  (
    message?.conversation ||
    message?.extendedTextMessage?.text ||
    message?.imageMessage?.caption ||
    message?.videoMessage?.caption ||
    ''
  ).trim();

const isGroup = (jid) => typeof jid === 'string' && jid.endsWith('@g.us');
const isBroadcast = (jid) =>
  typeof jid === 'string' && (jid === 'status@broadcast' || jid.includes('@broadcast'));

async function renderQrPng(qr) {
  try {
    await mkdir(runtimeDir, { recursive: true });
    await QRCode.toFile(qrPngPath, qr, { type: 'png', margin: 1, width: 512, color: { dark: '#000000', light: '#ffffff' } });
    console.log(`[whatsapp] qr pendiente en ${qrPngPath}`);
  } catch (err) {
    console.log(`[whatsapp][warn] no se pudo generar PNG del QR: ${err.message}`);
  }
}

const clearQrPng = () => rm(qrPngPath, { force: true }).catch(() => {});

export async function connect({ onMessage }) {
  await mkdir(authDir, { recursive: true });
  const { state, saveCreds } = await useMultiFileAuthState(authDir);
  const { version } = await fetchLatestBaileysVersion().catch(() => ({ version: undefined }));

  setState(States.AUTHENTICATING);
  let reconnectAttempts = 0;
  let sock;

  const start = async () => {
    sock = makeWASocket({
      version,
      auth: state,
      logger,
      markOnlineOnConnect: false,
      syncFullHistory: false,
      generateHighQualityLinkPreview: false,
      browser: ['AIF369 WhatsApp Agent (agent01)', 'Chrome', '1.0.0'],
    });
    wa.socket = sock;

    sock.ev.on('creds.update', saveCreds);

    sock.ev.on('connection.update', async (update) => {
      const { connection, lastDisconnect, qr } = update;

      if (qr) {
        setState(States.WAITING_FOR_QR);
        console.log('[whatsapp] esperando vinculacion (QR). Escanea con WhatsApp > Dispositivos vinculados:');
        qrcode.generate(qr, { small: true });
        await renderQrPng(qr);
      }

      if (connection === 'open') {
        reconnectAttempts = 0;
        wa.me = sock.user?.id || null;
        await clearQrPng();
        setState(States.CONNECTED);
        setState(States.READY, `jid=${String(sock.user?.jid || sock.user?.id || '').split(':')[0]}@s.whatsapp.net`);
        console.log('[whatsapp] ready. El agente esta atendiendo.');
      }

      if (connection === 'close') {
        const statusCode = lastDisconnect?.error?.output?.statusCode;
        setState(States.DISCONNECTED, `code=${statusCode ?? 'n/a'}`);

        if (statusCode === DisconnectReason.loggedOut) {
          setState(States.ERROR, 'logged_out');
          console.error('[whatsapp] sesion cerrada en el telefono. Se requiere vincular de nuevo (QR).');
          await clearQrPng();
          process.exit(1);
        }

        reconnectAttempts += 1;
        const delay = Math.min(30000, 2000 * reconnectAttempts);
        console.log(`[whatsapp] reconectando en ${delay}ms...`);
        setTimeout(() => start().catch((err) => console.error(`[whatsapp] reconnect error: ${err.message}`)), delay);
      }
    });

    sock.ev.on('messages.upsert', async ({ messages, type }) => {
      if (type !== 'notify') return;

      for (const m of messages) {
        try {
          if (!m.message || m.key.fromMe) continue;

          const jid = m.key.remoteJid || '';
          if (!jid || isBroadcast(jid)) continue;
          if (isGroup(jid) && !config.allowGroups) continue;
          if (jid.endsWith('@newsletter')) continue;

          const text = extractText(m.message);

          const normalized = normalizeInbound({
            chatJid: jid,
            msgId: m.key.id,
            sender: m.key.participant || jid,
            pushName: m.pushName || '',
            text,
            timestamp: m.messageTimestamp,
          });

          console.log(
            `[whatsapp] inbound from=${maskSender(normalized.sender_id)} type=${normalized.type} msg=${String(normalized.message_id || '').slice(0, 8)}`
          );
          markInbound();
          await onMessage(normalized);
        } catch (err) {
          console.log(`[whatsapp][warn] message processing failed: ${err.message}`);
        }
      }
    });
  };

  await start();
  return {
    get socket() {
      return sock;
    },
  };
}
