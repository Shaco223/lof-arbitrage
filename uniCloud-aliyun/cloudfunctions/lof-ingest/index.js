'use strict';

const { ok, fail } = require('./response');

exports.main = async (event) => {
  const token = getHeader(event, 'x-ingest-token') || event.XIngestToken || event.token;
  const expected = process.env.UNICLOUD_INGEST_TOKEN;
  if (!expected || token !== expected) return fail(4010, 'unauthorized');

  const body = parseBody(event);
  const validation = validatePayload(body);
  if (!validation.valid) return fail(4001, 'invalid params', { reason: validation.reason });
  const maxBatchSize = parseInt(process.env.MAX_INGEST_BATCH_SIZE || '100', 10);
  if (body.items.length > maxBatchSize) return fail(4290, 'rate limited');

  try {
    const db = uniCloud.database();
    const docs = body.items.map((item) => ({
      code: item.code,
      ts: body.ts,
      price: item.price,
      iopv: item.iopv,
      premium: item.premium,
      coverage: item.coverage,
      source_quality: item.source_quality || 'ok'
    }));

    await db.collection('lof_realtime').add(docs);
    return ok({ accepted: docs.length, rejected: 0 });
  } catch (error) {
    console.error(error);
    return fail(5000, 'server error');
  }
};

function parseBody(event) {
  if (!event) return {};
  if (event.body) {
    if (typeof event.body === 'string') {
      try { return JSON.parse(event.body); } catch (error) { return {}; }
    }
    return event.body;
  }
  return event;
}

function getHeader(event, key) {
  const headers = (event && (event.headers || event.headersParameters)) || {};
  const lowerKey = key.toLowerCase();
  for (const headerName of Object.keys(headers)) {
    if (headerName.toLowerCase() === lowerKey) return headers[headerName];
  }
  return undefined;
}

function validatePayload(body) {
  if (!body || !body.ts || !Array.isArray(body.items)) return { valid: false, reason: 'missing ts/items' };
  for (const item of body.items) {
    if (!/^\d{6}$/.test(String(item.code || ''))) return { valid: false, reason: 'invalid code' };
    for (const field of ['price', 'iopv', 'premium', 'coverage']) {
      if (typeof item[field] !== 'number' || Number.isNaN(item[field])) return { valid: false, reason: `invalid ${field}` };
    }
    if (item.source_quality && !['ok', 'degraded', 'stale'].includes(item.source_quality)) {
      return { valid: false, reason: 'invalid source_quality' };
    }
  }
  return { valid: true };
}
