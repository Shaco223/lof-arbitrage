'use strict';

const assert = require('assert');
const fs = require('fs');
const os = require('os');
const path = require('path');

const { createLocalApiServer } = require('../local-api-server');

async function run() {
  const outputDir = fs.mkdtempSync(path.join(os.tmpdir(), 'lof-api-real-snapshot-'));
  const snapshotFile = path.join(outputDir, 'local-minute-snapshots-v2.jsonl');
  fs.writeFileSync(snapshotFile, JSON.stringify({
    ts: '2026-06-19T10:31:00+08:00',
    items: [
      { code: '161725', price: 1.234, iopv: 1.2, premium: 0.028333, coverage: 1, source_quality: 'ok' },
      {
        code: '510900',
        price: 1.08,
        iopv: null,
        premium: null,
        coverage: 1,
        source_quality: 'ok',
        nav_official: 1.0,
        nav_official_date: '2026-07-01',
        qdii_estimate_nav: 1.0302,
        qdii_estimate_premium: 0.04834,
        qdii_reference_index_code: 'hkHSCEI',
        qdii_reference_index_name: '????????',
        qdii_reference_index_change_pct: 0.02,
        qdii_fx_change_pct: 0.01,
        qdii_estimate_quality: 'high',
        qdii_estimate_source: 'reference_index_estimate',
        qdii_nav_date: '2026-07-01'
      }
    ]
  }) + '\n', 'utf8');

  const server = createLocalApiServer({ minuteSnapshotFile: snapshotFile });
  await listen(server);
  const baseUrl = `http://127.0.0.1:${server.address().port}`;

  try {
    const list = await requestJson(`${baseUrl}/lof-list?sort=code`);
    const item = list.data.items.find((row) => row.code === '161725');
    assert.strictEqual(item.price, 1.234);
    assert.strictEqual(item.iopv, 1.2);
    assert.strictEqual(item.premium, 0.028333);
    assert.strictEqual(item.source_quality, 'ok');

    const qdiiList = await requestJson(`${baseUrl}/lof-list?sort=code&type=qdii`);
    assert.ok(qdiiList.data.items.length >= 5);
    const qdiiItem = qdiiList.data.items.find((row) => row.code === '510900');
    assert.ok(qdiiItem, '510900 should be present from watchlist metadata + snapshot');
    assert.strictEqual(qdiiItem.qdii_estimate_nav, 1.0302);

    const detail = await requestJson(`${baseUrl}/lof-detail?code=161725`);
    assert.strictEqual(detail.data.realtime.price, 1.234);
    assert.strictEqual(detail.data.realtime.premium, 0.028333);

    console.log('local api real snapshot test passed');
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

async function requestJson(url) {
  const response = await fetch(url);
  assert.strictEqual(response.status, 200);
  return response.json();
}

run().catch((error) => {
  console.error(error);
  process.exit(1);
});
