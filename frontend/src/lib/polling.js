export function pollJob(id, onData, onDone, intervalMs = 2000) {
  let cancelled = false;
  let timeoutId = null;

  async function poll() {
    if (cancelled) return;
    const data = await getJob(id);
    onData(data);
    if (data.status === "succeeded" || data.status === "failed") {
      onDone(data);
      return;
    }
    timeoutId = setTimeout(poll, intervalMs);
  }

  timeoutId = setTimeout(poll, intervalMs);
  return () => {
    cancelled = true;
    if (timeoutId) clearTimeout(timeoutId);
  };
}
