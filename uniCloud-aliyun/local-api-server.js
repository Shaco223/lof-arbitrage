'use strict';

const http = require('http');
const path = require('path');
const { URL } = require('url');
const fs = require('fs');
const { createMockUniCloud } = require('./tests/mock-unicloud');
const { loadLatestMinuteSnapshot } = require('./local-minute-snapshots');

const SAMPLE_DATASET_PATH = path.join(__dirname, 'tests', 'sample-dataset.json');
// Unified default: daemon/real-watchlist writes this file; local-api reads it
// without requiring LOCAL_MINUTE_SNAPSHOT_FILE so `daemon + local-api` works out of the box.
const DEFAULT_MINUTE_SNAPSHOT_FILE = path.join(__dirname, '..', 'outputs', 'local-minute-snapshots-watchlist-v2.jsonl');

function readSampleDatasetSync() {
  const text = fs.readFileSync(SAMPLE_DATASET_PATH, 'utf8');
  return JSON.parse(text);
}

const DEFAULT_PORT = 8787;
const DEFAULT_TOKEN = 'local-dev-token';
const STATE_CACHE_TTL_MS = 1000;

const HANDLER_PATHS = {
  '/lof-list': require.resolve('./cloudfunctions/lof-list/index'),
  '/lof-detail': require.resolve('./cloudfunctions/lof-detail/index'),
  '/lof-history': require.resolve('./cloudfunctions/lof-history/index'),
  '/lof-ingest': require.resolve('./cloudfunctions/lof-ingest/index')
};

function loadHandler(pathname, freshRequire) {
  const modulePath = HANDLER_PATHS[pathname];
  if (!modulePath) return null;
  if (freshRequire) {
    // Drop the handler and any of its sibling helpers (response.js, fallback-list.json, etc.)
    // so module-level caches inside the cloud function reset on each request.
    const dirPrefix = path.dirname(modulePath) + path.sep;
    for (const key of Object.keys(require.cache)) {
      if (key === modulePath || key.startsWith(dirPrefix)) {
        delete require.cache[key];
      }
    }
  }
  // eslint-disable-next-line global-require
  return require(modulePath);
}

function createLocalApiServer(options = {}) {
  const explicitDataset = options.dataset || null;
  const explicitSnapshotFile = options.minuteSnapshotFile;
  const token = options.token || process.env.UNICLOUD_INGEST_TOKEN || DEFAULT_TOKEN;
  const maxBatchSize = String(options.maxBatchSize || process.env.MAX_INGEST_BATCH_SIZE || '100');

  process.env.UNICLOUD_INGEST_TOKEN = token;
  process.env.MAX_INGEST_BATCH_SIZE = maxBatchSize;

  let cache = { datasetMtimeMs: -1, snapshotMtimeMs: -1, snapshotFile: null, t: 0, state: null };

  function getFreshState() {
    const snapshotFile = explicitSnapshotFile || process.env.LOCAL_MINUTE_SNAPSHOT_FILE || DEFAULT_MINUTE_SNAPSHOT_FILE;
    let snapshotMtimeMs = 0;
    if (snapshotFile) {
      try { snapshotMtimeMs = fs.statSync(snapshotFile).mtimeMs; } catch (_) { snapshotMtimeMs = 0; }
    }
    let datasetMtimeMs = 0;
    if (!explicitDataset) {
      try { datasetMtimeMs = fs.statSync(SAMPLE_DATASET_PATH).mtimeMs; } catch (_) { datasetMtimeMs = 0; }
    }
    const now = Date.now();
    if (
      cache.state &&
      cache.snapshotFile === snapshotFile &&
      cache.snapshotMtimeMs === snapshotMtimeMs &&
      cache.datasetMtimeMs === datasetMtimeMs &&
      (now - cache.t) < STATE_CACHE_TTL_MS
    ) {
      return { state: cache.state, fresh: false };
    }
    const baseDataset = explicitDataset || readSampleDatasetSync();
    const state = applyMinuteSnapshot(clone(baseDataset), snapshotFile);
    cache = { datasetMtimeMs, snapshotMtimeMs, snapshotFile, t: now, state };
    return { state, fresh: true };
  }

  // Initialize global.uniCloud once so non-HTTP consumers still see a sane mock.
  global.uniCloud = createMockUniCloud(getFreshState().state);

  return http.createServer(async (req, res) => {
    const requestUrl = new URL(req.url, `http://${req.headers.host || 'localhost'}`);

    if (!HANDLER_PATHS[requestUrl.pathname]) {
      writeJson(res, 404, { code: 4040, message: 'not found', data: {} });
      return;
    }

    try {
      const { state, fresh } = getFreshState();
      // Refresh state from JSONL on every request (with <=1s mtime micro-cache).
      global.uniCloud = createMockUniCloud(state);
      // When dataset changed, also drop cloud-function module caches so any
      // module-level TTL caches inside handlers (e.g. lof-list 60s cache)
      // pick up the new state immediately. Cloud function source files are
      // unchanged; this only resets local require cache.
      const handler = loadHandler(requestUrl.pathname, fresh);
      const bodyText = await readBody(req);
      const event = {
        queryStringParameters: Object.fromEntries(requestUrl.searchParams.entries()),
        rawQueryString: requestUrl.searchParams.toString(),
        headers: req.headers,
        httpMethod: req.method,
        body: bodyText ? parseJsonBody(bodyText) : undefined
      };
      const payload = await handler.main(event);
      writeJson(res, 200, payload);
    } catch (error) {
      console.error(error);
      writeJson(res, 500, { code: 5000, message: 'server error', data: {} });
    }
  });
}

function applyMinuteSnapshot(state, explicitSnapshotFile) {
  const snapshotFile = explicitSnapshotFile || process.env.LOCAL_MINUTE_SNAPSHOT_FILE || DEFAULT_MINUTE_SNAPSHOT_FILE;
  if (!snapshotFile) return state;
  let snapshot = null;
  try {
    snapshot = loadLatestMinuteSnapshot(snapshotFile);
  } catch (error) {
    console.warn(`[local-api-server] failed to read snapshot ${snapshotFile}: ${error.message}`);
    return state;
  }
  if (!snapshot || !Array.isArray(snapshot.items) || !snapshot.items.length) return state;

  const byCode = new Map(snapshot.items.map((item) => [String(item.code), item]));
  state.lof_realtime = (state.lof_realtime || []).map((row) => {
    const item = byCode.get(String(row.code));
    if (!item) return row;
    return {
      ...row,
      ts: snapshot.ts,
      price: item.price,
      iopv: item.iopv,
      premium: item.premium,
      coverage: item.coverage,
      source_quality: item.source_quality || 'degraded'
    };
  });
  return state;
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    req.on('data', (chunk) => chunks.push(chunk));
    req.on('end', () => resolve(Buffer.concat(chunks).toString('utf8')));
    req.on('error', reject);
  });
}

function parseJsonBody(bodyText) {
  try {
    return JSON.parse(bodyText);
  } catch (error) {
    return bodyText;
  }
}

function writeJson(res, statusCode, payload) {
  const body = JSON.stringify(payload);
  res.writeHead(statusCode, {
    'Content-Type': 'application/json; charset=utf-8',
    'Cache-Control': 'no-store',
    'Pragma': 'no-cache',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type, X-Ingest-Token',
    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
  });
  res.end(body);
}

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function start() {
  const port = Number(process.env.LOCAL_API_PORT || process.env.PORT || DEFAULT_PORT);
  const server = createLocalApiServer();
  server.listen(port, '127.0.0.1', () => {
    console.log(`LOF local API listening on http://127.0.0.1:${port}`);
    console.log(`Functions: lof-list / lof-detail / lof-history / lof-ingest`);
    console.log(`Local ingest token env: UNICLOUD_INGEST_TOKEN (default: ${DEFAULT_TOKEN})`);
  });
}

if (require.main === module) start();

module.exports = { createLocalApiServer, DEFAULT_PORT, DEFAULT_TOKEN, applyMinuteSnapshot };