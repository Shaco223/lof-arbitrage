'use strict';

const assert = require('assert');
const fs = require('fs');
const os = require('os');
const path = require('path');

const { appendMinuteSnapshot, loadLatestMinuteSnapshot } = require('../local-minute-snapshots');

function run() {
  const outputDir = fs.mkdtempSync(path.join(os.tmpdir(), 'lof-real-snapshots-'));
  const outputPath = path.join(outputDir, 'local-minute-snapshots-v2.jsonl');
  const realSnapshot = {
    ts: '2026-06-19T10:31:00+08:00',
    items: [
      { code: '161725', price: 1.234, iopv: 1.2, premium: 0.028333, coverage: 1, source_quality: 'ok' },
      { code: '161005', price: 2.0, iopv: null, premium: null, coverage: 0.62, source_quality: 'degraded' }
    ]
  };

  const result = appendMinuteSnapshot({ outputPath, snapshot: realSnapshot });
  assert.strictEqual(result.snapshot.items.length, 2);

  const latest = loadLatestMinuteSnapshot(outputPath);
  assert.strictEqual(latest.ts, '2026-06-19T10:31:00+08:00');
  assert.strictEqual(latest.items[0].code, '161725');
  assert.strictEqual(latest.items[0].premium, 0.028333);
  assert.strictEqual(latest.items[1].source_quality, 'degraded');

  console.log('real minute snapshot override test passed');
}

run();
