'use strict';

const assert = require('assert');

const { createMockUniCloud } = require('./mock-unicloud');

async function run() {
  const dataset = require('./sample-dataset');
  const lofHistoryPath = require.resolve('../cloudfunctions/lof-history/index');
  delete require.cache[lofHistoryPath];

  const seed = { ...dataset, lof_history: dataset.lof_history.filter((item) => item.code === '161725').slice(0, 1) };
  global.uniCloud = createMockUniCloud(seed);
  const lofHistory = require('../cloudfunctions/lof-history/index');

  const response = await lofHistory.main({ query: { code: '161725', days: '30' } });

  assert.strictEqual(response.code, 0);
  assert.strictEqual(response.data.granularity, 'day');
  assert.strictEqual(response.data.items.length, 30);
  assert.ok(response.data.items.every((item) => typeof item.date === 'string'));
  assert.ok(response.data.items.every((item) => typeof item.close_price === 'number'));
  assert.ok(response.data.items.every((item) => typeof item.official_nav === 'number'));
  assert.ok(response.data.items.every((item) => typeof item.premium_close === 'number'));
  assert.ok(response.data.items.every((item) => typeof item.premium_pctile_30d === 'number'));
  // PRD 1.2.3 ?6.3: the two new fields are always present and null-safe; on the
  // fallback path they are NEVER synthesized (AC-H6) -> must be null.
  assert.ok(response.data.items.every((item) => 'premium_estimate_close' in item));
  assert.ok(response.data.items.every((item) => 'premium_deviation' in item));
  assert.ok(response.data.items.every((item) => item.premium_estimate_close === null));
  assert.ok(response.data.items.every((item) => item.premium_deviation === null));

  // Real sedimented rows (PRD 1.2.3 day-by-day) must pass the two fields through.
  const realSeed = {
    ...dataset,
    lof_history: [
      { code: '161725', date: '2026-06-22', close_price: 0.527, official_nav: 0.5289,
        premium_close: 0.003781, premium_pctile_30d: null,
        premium_estimate_close: 0.012, premium_deviation: 0.008219 },
      { code: '161725', date: '2026-06-23', close_price: 0.520, official_nav: null,
        premium_close: null, premium_pctile_30d: null,
        premium_estimate_close: 0.018, premium_deviation: null }
    ]
  };
  delete require.cache[lofHistoryPath];
  global.uniCloud = createMockUniCloud(realSeed);
  const lofHistory2 = require('../cloudfunctions/lof-history/index');
  const realResp = await lofHistory2.main({ query: { code: '161725', days: '2' } });
  assert.strictEqual(realResp.code, 0);
  const byDate = {};
  for (const it of realResp.data.items) byDate[it.date] = it;
  assert.strictEqual(byDate['2026-06-22'].premium_estimate_close, 0.012);
  assert.strictEqual(byDate['2026-06-22'].premium_deviation, 0.008219);
  // T day: estimate present, deviation null (official nav T+1 pending).
  assert.strictEqual(byDate['2026-06-23'].premium_estimate_close, 0.018);
  assert.strictEqual(byDate['2026-06-23'].premium_deviation, null);

  console.log('history fallback test passed');
}

run().catch((error) => {
  console.error(error);
  process.exit(1);
});
