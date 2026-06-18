'use strict';

const http = require('http');
const { URL } = require('url');
const { createMockUniCloud } = require('./tests/mock-unicloud');
const { loadLatestMinuteSnapshot } = require('./local-minute-snapshots');

const dataset = require('./tests/sample-dataset.json');
const lofList = require('./cloudfunctions/lof-list/index');
const lofDetail = require('./cloudfunctions/lof-detail/index');
const lofHistory = require('./cloudfunctions/lof-history/index');
const lofIngest = require('./cloudfunctions/lof-ingest/index');

const DEFAULT_PORT = 8787;
const DEFAULT_TOKEN = 'local-dev-token';
const ROUTES = {
  '/lof-list': lofList,
  '/lof-detail': lofDetail,
  '/lof-history': lofHistory,
  '/lof-ingest': lofIngest
};

function createLocalApiServer(options = {}) {
  const state = applyMinuteSnapshot(clone(options.dataset || dataset), options.minuteSnapshotFile);
  const token = options.token || process.env.UNICLOUD_INGEST_TOKEN || DEFAULT_TOKEN;
  const maxBatchSize = String(options.maxBatchSize || process.env.MAX_INGEST_BATCH_SIZE || '100');

  global.uniCloud = createMockUniCloud(state);
  process.env.UNICLOUD_INGEST_TOKEN = token;
  process.env.MAX_INGEST_BATCH_SIZE = maxBatchSize;

  return http.createServer(async (req, res) => {
    const requestUrl = new URL(req.url, `http://${req.headers.host || 'localhost'}`);
    const handler = ROUTES[requestUrl.pathname];

    if (!handler) {
      writeJson(res, 404, { code: 4040, message: 'not found', data: {} });
      return;
    }

    try {
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
  const snapshotFile = explicitSnapshotFile || process.env.LOCAL_MINUTE_SNAPSHOT_FILE;
  if (!snapshotFile) return state;
  const snapshot = loadLatestMinuteSnapshot(snapshotFile);
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
