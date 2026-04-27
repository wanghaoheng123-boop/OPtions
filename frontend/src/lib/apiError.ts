export function extractApiErrorMessage(err: any, fallback: string): string {
  const responseData = err?.response?.data;
  const detail = responseData?.detail ?? responseData?.message;

  if (typeof detail === 'string' && detail.trim()) return detail;
  if (Array.isArray(detail)) return JSON.stringify(detail);
  if (detail != null) return JSON.stringify(detail);

  const rawData = typeof responseData === 'string' ? responseData.trim() : '';
  if (rawData) {
    if (rawData.startsWith('<!DOCTYPE') || rawData.startsWith('<html')) {
      return `${fallback} (server returned HTML error page)`;
    }
    return rawData.slice(0, 240);
  }

  if (!err?.response) {
    const msg = err?.message || '';
    if (msg.includes('Network Error') || err?.code === 'ERR_NETWORK') {
      return 'Cannot reach API. For local dev start backend on port 8005.';
    }
    return msg || `${fallback} (no response)`;
  }

  return err?.message || fallback;
}
