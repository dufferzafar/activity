/*
Open https://photos.google.com with your browser's developer tools open

And paste the following code into the console:
*/

(async () => {
  console.log('[GPTK] Starting frequency counter (>= 2020-01-01)...');

  const startMs = Date.UTC(2020, 0, 1); // after 2019
  const counts = new Map();

  let nextPageId = null;
  let pageCount = 0;
  let totalKept = 0;
  const startedAt = Date.now();

  do {
    const page = await gptkApi.getItemsByTakenDate(timestamp = null, source = null, pageId = nextPageId);
    const items = page?.items ?? [];
    let keptThisPage = 0;

    for (const item of items) {
      if (item?.timestamp >= startMs) {
        const tz = typeof item.timezoneOffset === 'number' ? item.timezoneOffset : 0;
        const local = new Date(item.timestamp + tz);
        const yyyy = local.getUTCFullYear();
        const mm = String(local.getUTCMonth() + 1).padStart(2, '0');
        const dd = String(local.getUTCDate()).padStart(2, '0');
        const key = `${yyyy}-${mm}-${dd}`;
        counts.set(key, (counts.get(key) || 0) + 1);
        keptThisPage++;
        totalKept++;
      }
    }

    pageCount++;
    nextPageId = page?.nextPageId ?? null;

    const lastTs = page?.lastItemTimestamp;
    const shouldStop = typeof lastTs === 'number' && lastTs < startMs;

    console.log(`[GPTK] Page ${pageCount}: scanned ${items.length}, kept ${keptThisPage}, total kept ${totalKept}. nextPageId=${Boolean(nextPageId)}${shouldStop ? ' (reached <2020 — stopping)' : ''}`);
    // console.log(counts);
    if (shouldStop) break;

    await new Promise(r => setTimeout(r, 50)); // small yield
  } while (nextPageId);

  const entries = Array.from(counts.entries()).sort((a, b) => a[0].localeCompare(b[0]));
  console.log('[GPTK] Done in', ((Date.now() - startedAt) / 1000).toFixed(1), 's. Unique dates:', entries.length, 'Total items:', totalKept);
  console.table(entries.map(([date, count]) => ({ date, count })));

  // Convenience: keep results on window and provide copy helpers
  window.__gptk_freq__ = entries;
  console.log('[GPTK] Results available as window.__gptk_freq__ (array of [date, count]).');
  console.log('[GPTK] Copy JSON:', 'copy(JSON.stringify(Object.fromEntries(window.__gptk_freq__), null, 2))');
  console.log('[GPTK] Copy CSV:', 'copy(window.__gptk_freq__.map(r => r.join(",")).join("\\n"))');
})();