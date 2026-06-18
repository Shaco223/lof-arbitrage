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

  console.log('history fallback test passed');
}

run().catch((error) => {
  console.error(error);
  process.exit(1);
});
