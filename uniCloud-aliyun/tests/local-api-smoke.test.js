'use strict';

const assert = require('assert');

const { createMockUniCloud } = require('./mock-unicloud');

async function run() {
  const dataset = require('./sample-dataset');
  global.uniCloud = createMockUniCloud(dataset);
  process.env.UNICLOUD_INGEST_TOKEN = 'secret';
  process.env.MAX_INGEST_BATCH_SIZE = '100';

  const lofList = require('../cloudfunctions/lof-list/index');
  const lofDetail = require('../cloudfunctions/lof-detail/index');
  const lofHistory = require('../cloudfunctions/lof-history/index');
  const lofIngest = require('../cloudfunctions/lof-ingest/index');

  const list = await lofList.main({ query: { sort: 'code' } });
  assert.strictEqual(list.code, 0);
  assert.strictEqual(list.data.items.length, 30);
  assert.strictEqual(list.data.items[0].code, '160119');

  const detail = await lofDetail.main({ query: { code: '161725' } });
  assert.strictEqual(detail.code, 0);
  assert.ok(detail.data.coverage_breakdown);
  assert.ok(Array.isArray(detail.data.benchmark_components));

  const history = await lofHistory.main({ query: { code: '161725', days: '30' } });
  assert.strictEqual(history.code, 0);
  assert.strictEqual(history.data.granularity, 'day');
  assert.strictEqual(history.data.items.length, 30);

  const unauthorized = await lofIngest.main({ headers: { 'X-Ingest-Token': 'bad' }, body: {} });
  assert.strictEqual(unauthorized.code, 4010);

  const invalid = await lofIngest.main({ headers: { 'X-Ingest-Token': 'secret' }, body: { ts: dataset.ts, items: [{}] } });
  assert.strictEqual(invalid.code, 4001);

  const accepted = await lofIngest.main({
    headers: { 'X-Ingest-Token': 'secret' },
    body: {
      ts: dataset.ts,
      items: dataset.lof_realtime.map((item) => ({
        code: item.code,
        price: item.price,
        iopv: item.iopv,
        premium: item.premium,
        coverage: item.coverage,
        source_quality: item.source_quality
      }))
    }
  });
  assert.strictEqual(accepted.code, 0);
  assert.strictEqual(accepted.data.accepted, 30);
  assert.strictEqual(accepted.data.rejected, 0);

  console.log('local api smoke passed');
}

run().catch((error) => {
  console.error(error);
  process.exit(1);
});
