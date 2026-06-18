'use strict';

const assert = require('assert');
const { createLocalApiServer, DEFAULT_TOKEN } = require('../local-api-server');

async function run() {
  const server = createLocalApiServer({ token: DEFAULT_TOKEN });
  await listen(server);
  const baseUrl = `http://127.0.0.1:${server.address().port}`;

  try {
    const list = await requestJson(`${baseUrl}/lof-list?sort=code`);
    assert.strictEqual(list.code, 0);
    assert.strictEqual(list.data.items.length, 30);
    assert.strictEqual(list.data.items[0].code, '160119');

    const detail = await requestJson(`${baseUrl}/lof-detail?code=${list.data.items[0].code}`);
    assert.strictEqual(detail.code, 0);
    assert.ok(detail.data.coverage_breakdown);
    assert.ok(detail.data.realtime);

    const history = await requestJson(`${baseUrl}/lof-history?code=${list.data.items[0].code}&days=30`);
    assert.strictEqual(history.code, 0);
    assert.strictEqual(history.data.granularity, 'day');
    assert.ok(history.data.items.length >= 20);

    const unauthorized = await requestJson(`${baseUrl}/lof-ingest`, {
      method: 'POST',
      body: JSON.stringify({ ts: '2026-06-18T10:31:00+08:00', items: [] })
    });
    assert.strictEqual(unauthorized.code, 4010);

    const accepted = await requestJson(`${baseUrl}/lof-ingest`, {
      method: 'POST',
      headers: { 'X-Ingest-Token': DEFAULT_TOKEN },
      body: JSON.stringify({
        ts: list.data.ts,
        items: list.data.items.map((item) => ({
          code: item.code,
          price: item.price,
          iopv: item.iopv,
          premium: item.premium,
          coverage: item.coverage,
          source_quality: item.source_quality
        }))
      })
    });
    assert.strictEqual(accepted.code, 0);
    assert.strictEqual(accepted.data.accepted, 30);
    assert.strictEqual(accepted.data.rejected, 0);

    console.log('local http smoke passed');
  } finally {
    await close(server);
  }
}

function listen(server) {
  return new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
}

function close(server) {
  return new Promise((resolve, reject) => server.close((error) => error ? reject(error) : resolve()));
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, {
    method: options.method || 'GET',
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    body: options.body
  });
  assert.strictEqual(response.status, 200);
  return response.json();
}

run().catch((error) => {
  console.error(error);
  process.exit(1);
});
