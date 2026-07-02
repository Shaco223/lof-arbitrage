'use strict';

const assert = require('assert');
const path = require('path');

const { createLocalApiServer } = require('../local-api-server');

const QDII_FIELDS = [
  'qdii_estimate_nav',
  'qdii_estimate_premium',
  'qdii_reference_index_code',
  'qdii_reference_index_name',
  'qdii_reference_index_change_pct',
  'qdii_fx_change_pct',
  'qdii_estimate_quality',
  'qdii_estimate_source',
  'qdii_nav_date'
];

async function run() {
  const dataset = {
    ts: '2026-07-02T10:31:00+08:00',
    lof_meta: [
      { code: '510900', name: 'H?ETF', type: 'qdii', status: 'active', scale_yi: 1, benchmark_raw: '' },
      { code: '162411', name: '华宝油气LOF', type: 'industry', status: 'active', scale_yi: 1, benchmark_raw: '' }
    ],
    lof_realtime: [
      {
        code: '510900',
        ts: '2026-07-02T10:31:00+08:00',
        price: 1.08,
        iopv: null,
        premium: null,
        nav_official: 1.0,
        nav_official_date: '2026-07-01',
        coverage: 1,
        source_quality: 'ok',
        qdii_estimate_nav: 1.0302,
        qdii_estimate_premium: 0.04834,
        qdii_reference_index_code: 'hkHSCEI',
        qdii_reference_index_name: '恒生中国企业指数',
        qdii_reference_index_change_pct: 0.02,
        qdii_fx_change_pct: 0.01,
        qdii_estimate_quality: 'high',
        qdii_estimate_source: 'reference_index_estimate',
        qdii_nav_date: '2026-07-01'
      },
      {
        code: '162411',
        ts: '2026-07-02T10:31:00+08:00',
        price: 0.8,
        iopv: 0.81,
        premium: -0.012346,
        nav_official: 0.82,
        nav_official_date: '2026-07-01',
        coverage: 1,
        source_quality: 'ok',
        qdii_estimate_nav: null,
        qdii_estimate_premium: null,
        qdii_reference_index_code: null,
        qdii_reference_index_name: null,
        qdii_reference_index_change_pct: null,
        qdii_fx_change_pct: null,
        qdii_estimate_quality: 'unavailable',
        qdii_estimate_source: null,
        qdii_nav_date: null
      }
    ],
    lof_history: [
      { code: '510900', date: '2026-07-01', premium_pctile_30d: null },
      { code: '162411', date: '2026-07-01', premium_pctile_30d: null }
    ],
    lof_holdings: []
  };

  const server = createLocalApiServer({ dataset, minuteSnapshotFile: path.join(__dirname, 'missing-qdiitest-snapshot.jsonl') });
  await listen(server);
  const baseUrl = `http://127.0.0.1:${server.address().port}`;

  try {
    const list = await requestJson(`${baseUrl}/lof-list?sort=code`);
    const high = list.data.items.find((item) => item.code === '510900');
    const nonHigh = list.data.items.find((item) => item.code === '162411');

    for (const field of QDII_FIELDS) assert.ok(field in high, `list high missing ${field}`);
    assert.strictEqual(high.qdii_estimate_nav, 1.0302);
    assert.strictEqual(high.qdii_estimate_premium, 0.04834);
    assert.strictEqual(high.iopv, null, 'qdii estimate must not pollute iopv');
    assert.strictEqual(high.premium, null, 'qdii estimate must not pollute premium');
    assert.strictEqual(nonHigh.qdii_estimate_nav, null);
    assert.strictEqual(nonHigh.qdii_estimate_premium, null);

    const qdiiList = await requestJson(`${baseUrl}/lof-list?sort=code&type=qdii`);
    assert.strictEqual(qdiiList.data.items.length, 1);
    assert.strictEqual(qdiiList.data.items[0].code, '510900');

    const detail = await requestJson(`${baseUrl}/lof-detail?code=510900`);
    for (const field of QDII_FIELDS) assert.ok(field in detail.data, `detail missing ${field}`);
    assert.strictEqual(detail.data.qdii_reference_index_code, 'hkHSCEI');
    assert.strictEqual(detail.data.realtime.qdii_estimate_nav, 1.0302);
    assert.strictEqual(detail.data.realtime.iopv, null, 'realtime qdii estimate must not pollute iopv');

    console.log('local api qdii fields test passed');
  } finally {
    await close(server);
  }
}

function listen(server) {
  return new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
}

function close(server) {
  return new Promise((resolve, reject) => server.close((error) => (error ? reject(error) : resolve())));
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
