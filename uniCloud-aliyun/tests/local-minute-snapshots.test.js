'use strict';

const assert = require('assert');
const fs = require('fs');
const os = require('os');
const path = require('path');

const dataset = require('./sample-dataset.json');
const { appendMinuteSnapshot, buildMinuteSnapshot } = require('../local-minute-snapshots');

function run() {
  const outputDir = fs.mkdtempSync(path.join(os.tmpdir(), 'lof-minute-snapshots-'));
  const outputPath = path.join(outputDir, 'local-minute-snapshots-v2.jsonl');

  const first = buildMinuteSnapshot(dataset, '2026-06-18T10:31:00+08:00');
  assert.strictEqual(first.ts, '2026-06-18T10:31:00+08:00');
  assert.strictEqual(first.items.length, 30);
  assert.ok(first.items.every((item) => typeof item.code === 'string'));
  assert.ok(first.items.every((item) => typeof item.price === 'number'));
  assert.ok(first.items.every((item) => typeof item.iopv === 'number'));
  assert.ok(first.items.every((item) => typeof item.premium === 'number'));
  assert.ok(first.items.every((item) => typeof item.coverage === 'number'));

  appendMinuteSnapshot({ dataset, outputPath, ts: '2026-06-18T10:31:00+08:00' });
  appendMinuteSnapshot({ dataset, outputPath, ts: '2026-06-18T10:32:00+08:00' });

  const lines = fs.readFileSync(outputPath, 'utf8').trim().split(/\r?\n/).map((line) => JSON.parse(line));
  assert.strictEqual(lines.length, 2);
  assert.strictEqual(lines[0].ts, '2026-06-18T10:31:00+08:00');
  assert.strictEqual(lines[1].ts, '2026-06-18T10:32:00+08:00');
  assert.strictEqual(lines[0].items.length, 30);
  assert.strictEqual(lines[1].items.length, 30);

  console.log('local minute snapshots test passed');
}

run();
