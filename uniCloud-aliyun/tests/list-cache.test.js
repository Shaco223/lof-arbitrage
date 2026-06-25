'use strict';

const assert = require('assert');

const { createMockUniCloud } = require('./mock-unicloud');

async function run() {
  const dataset = require('./sample-dataset');
  const lofListPath = require.resolve('../cloudfunctions/lof-list/index');
  delete require.cache[lofListPath];

  const calls = [];
  global.uniCloud = createMockUniCloud(dataset, { onGet: (name) => calls.push(name) });
  const lofList = require('../cloudfunctions/lof-list/index');

  const first = await lofList.main({ query: { sort: 'code' } });
  const second = await lofList.main({ query: { sort: 'code' } });

  assert.strictEqual(first.code, 0);
  assert.strictEqual(second.code, 0);
  assert.ok(first.data.items.length >= 122, `expected >=122, got ${first.data.items.length}`);
  assert.ok(second.data.items.length >= 122, `expected >=122, got ${second.data.items.length}`);
  assert.deepStrictEqual(second, first);
  assert.deepStrictEqual(calls, ['lof_meta', 'lof_realtime', 'lof_history']);

  console.log('list cache test passed');
}

run().catch((error) => {
  console.error(error);
  process.exit(1);
});
