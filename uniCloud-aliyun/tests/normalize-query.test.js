'use strict';

const assert = require('assert');

const { normalizeQuery } = require('../cloudfunctions/lof-history/response');

function run() {
  assert.deepStrictEqual(normalizeQuery({ query: { code: '161725', days: '30' } }), { code: '161725', days: '30' });
  assert.deepStrictEqual(normalizeQuery({ queryStringParameters: { code: '161725', days: '30' } }), { code: '161725', days: '30' });
  assert.deepStrictEqual(normalizeQuery({ rawQueryString: 'code=161725&days=30&granularity=day' }), {
    code: '161725',
    days: '30',
    granularity: 'day'
  });
  assert.deepStrictEqual(normalizeQuery({ body: JSON.stringify({ code: '161725', days: 30 }) }), { code: '161725', days: 30 });

  console.log('normalize query test passed');
}

run();
