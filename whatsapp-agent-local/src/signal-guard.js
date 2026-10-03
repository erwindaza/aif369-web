const signal = { count: 0, lastLoggedAt: 0 };

const isSignalNoise = (value) => {
  const text = String(value ?? '');
  return (
    text.includes('Failed to decrypt message with any known session') ||
    text.startsWith('Session error:') ||
    (text.includes('libsignal/src/') && text.includes('at SessionCipher'))
  );
};

export function installSignalGuard() {
  const originalError = console.error.bind(console);
  console.error = (...args) => {
    if (isSignalNoise(args[0]) || isSignalNoise(args[1])) {
      signal.count += 1;
      const now = Date.now();
      if (now - signal.lastLoggedAt >= 30000) {
        signal.lastLoggedAt = now;
        originalError(
          `[whatsapp][warn] message decryption failed (recuperable, total=${signal.count})`
        );
      }
      return;
    }
    originalError(...args);
  };

  process.on('unhandledRejection', (reason) => {
    originalError(`[whatsapp][warn] recoverable signal session error: ${reason?.message || reason}`);
  });
  process.on('uncaughtException', (err) => {
    if (isSignalNoise(err?.message) || isSignalNoise(err?.stack)) {
      signal.count += 1;
      originalError(`[whatsapp][warn] recoverable signal session error (total=${signal.count})`);
      return;
    }
    originalError(`[whatsapp] uncaughtException: ${err?.stack || err}`);
  });
}

export const getSignalErrorCount = () => signal.count;
