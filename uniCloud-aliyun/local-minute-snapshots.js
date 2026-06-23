'use strict';

const fs = require('fs');
const path = require('path');

const DEFAULT_OUTPUT = path.resolve(__dirname, '..', 'outputs', 'local-minute-snapshots-v2.jsonl');
const DEFAULT_DATASET = require('./tests/sample-dataset.json');

function buildMinuteSnapshot(dataset = DEFAULT_DATASET, ts = new Date().toISOString()) {
  const realtimeRows = Array.isArray(dataset.lof_realtime) ? dataset.lof_realtime : [];
  const items = realtimeRows
    .slice(0, 30)
    .map(normalizeSnapshotItem);

  return { ts, items };
}

function appendMinuteSnapshot(options = {}) {
  const dataset = options.dataset || DEFAULT_DATASET;
  const outputPath = path.resolve(options.outputPath || process.env.LOCAL_MINUTE_SNAPSHOT_FILE || DEFAULT_OUTPUT);
  const ts = options.ts || process.env.LOCAL_MINUTE_SNAPSHOT_TS || new Date().toISOString();
  const snapshot = options.snapshot ? normalizeSnapshot(options.snapshot, ts) : buildMinuteSnapshot(dataset, ts);

  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  fs.appendFileSync(outputPath, JSON.stringify(snapshot) + '\n', 'utf8');
  return { outputPath, snapshot };
}

function loadLatestMinuteSnapshot(outputPath = process.env.LOCAL_MINUTE_SNAPSHOT_FILE || DEFAULT_OUTPUT) {
  const filePath = path.resolve(outputPath);
  if (!fs.existsSync(filePath)) return null;
  const lines = fs.readFileSync(filePath, 'utf8').split(/\r?\n/).filter((line) => line.trim());
  if (!lines.length) return null;
  return JSON.parse(lines[lines.length - 1]);
}

function normalizeSnapshot(snapshot, fallbackTs) {
  return {
    ts: snapshot.ts || fallbackTs,
    items: Array.isArray(snapshot.items) ? snapshot.items.map(normalizeSnapshotItem) : []
  };
}

function normalizeSnapshotItem(item) {
  return {
    code: String(item.code),
    price: nullableNumber(item.price),
    iopv: nullableNumber(item.iopv),
    premium: nullableNumber(item.premium),
    coverage: nullableNumber(item.coverage),
    source_quality: item.source_quality || 'ok',
    // Carry nav_official/nav_official_date so premium_nav uses the SAME time-frame
    // as price on the pure-JSONL read path (daemon not running).
    nav_official: nullableNumber(item.nav_official),
    nav_official_date: item.nav_official_date != null ? String(item.nav_official_date) : null
  };
}

function nullableNumber(value) {
  if (value === null || value === undefined || value === '') return null;
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

function parseArgs(argv) {
  const args = { outputPath: undefined, ts: undefined };
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === '--output' || arg === '--output-path') args.outputPath = argv[++index];
    else if (arg === '--ts') args.ts = argv[++index];
    else if (arg === '--help' || arg === '-h') args.help = true;
  }
  return args;
}

function printHelp() {
  console.log('Usage: node uniCloud-aliyun/local-minute-snapshots.js [--output outputs/local-minute-snapshots-v2.jsonl] [--ts 2026-06-18T10:31:00+08:00]');
}

function runCli() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) {
    printHelp();
    return;
  }
  const result = appendMinuteSnapshot(args);
  console.log(JSON.stringify({ outputPath: result.outputPath, ts: result.snapshot.ts, count: result.snapshot.items.length }));
}

if (require.main === module) runCli();

module.exports = { DEFAULT_OUTPUT, buildMinuteSnapshot, appendMinuteSnapshot, loadLatestMinuteSnapshot };
