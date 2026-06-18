'use strict';

const assert = require('assert');

async function run() {
  process.env.UNICLOUD_INGEST_TOKEN = 'secret';
  const ingest = require('../cloudfunctions/lof-ingest/index');

  const unauthorized = await ingest.main({ headers: { 'X-Ingest-Token': 'bad' }, body: {} });
  assert.strictEqual(unauthorized.code, 4010);

  const invalid = await ingest.main({ headers: { 'X-Ingest-Token': 'secret' }, body: { ts: '2026-06-18T10:31:00+08:00', items: [{}] } });
  assert.strictEqual(invalid.code, 4001);

  process.env.MAX_INGEST_BATCH_SIZE = '1';
  const limited = await ingest.main({
    headers: { 'X-Ingest-Token': 'secret' },
    body: {
      ts: '2026-06-18T10:31:00+08:00',
      items: [
        { code: '161725', price: 0.823, iopv: 0.805, premium: 0.0224, coverage: 1.0, source_quality: 'ok' },
        { code: '161005', price: 1.1, iopv: 1.0, premium: 0.1, coverage: 0.9, source_quality: 'ok' }
      ]
    }
  });
  assert.strictEqual(limited.code, 4290);

  console.log('contract smoke passed');
}

run().catch((error) => {
  console.error(error);
  process.exit(1);
});
