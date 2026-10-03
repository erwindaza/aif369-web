export const States = {
  STARTING: 'STARTING',
  AUTHENTICATING: 'AUTHENTICATING',
  WAITING_FOR_QR: 'WAITING_FOR_QR',
  CONNECTED: 'CONNECTED',
  READY: 'READY',
  DEGRADED: 'DEGRADED',
  DISCONNECTED: 'DISCONNECTED',
  ERROR: 'ERROR',
};

let current = States.STARTING;
const since = { at: Date.now() };
const messageHealth = {
  lastInboundAt: null,
  lastOutboundAt: null,
};

export function setState(next, detail) {
  if (next === current) return;
  current = next;
  since.at = Date.now();
  console.log(`[whatsapp] state=${next}${detail ? ` ${detail}` : ''}`);
}

export const getState = () => current;
export const getStateSince = () => new Date(since.at).toISOString();

export function markInbound() {
  messageHealth.lastInboundAt = new Date().toISOString();
}

export function markOutbound() {
  messageHealth.lastOutboundAt = new Date().toISOString();
}

export const getMessageHealth = () => ({ ...messageHealth });
