'use strict';

const fs = require('fs');
const path = require('path');

const DEFAULT_OUTPUT = path.resolve(__dirname, '..', 'outputs', 'local-minute-snapshots-v2.jsonl');
const DEFAULT_DATASET = require('./tests/sample-dataset.json');

function buildMinuteSnapshot(dataset = DEFAULT_DATASET, ts = new Date().toISOString()) {
  const realtimeRows = Array.isArray(dataset.lof_realtime) ? dataset.lof_realtime : [];
  const items = realtimeRows
    .slice(0, 30)
    .map((item) => ({
      code: String(item.code),
      price: Number(item.price),
      iopv: Number(item.iopv),
      premium: Number(item.premium),
      coverage: Number(item.coverage),
      source_quality: item.source_quality || 'ok'
    }));

  return { ts, items };
}

function appendMinuteSnapshot(options = {}) {
  const dataset = options.dataset || DEFAULT_DATASET;
  const outputPath = path.resolve(options.outputPath || process.env.LOCAL_MINUTE_SNAPSHOT_FILE || DEFAULT_OUTPUT);
  const ts = options.ts || process.env.LOCAL_MINUTE_SNAPSHOT_TS || new Date().toISOString();
  const snapshot = buildMinuteSnapshot(dataset, ts);

  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  fs.appendFileSync(outputPath, JSON.stringify(snapshot) + '\n', 'utf8');
  return { outputPath, snapshot };
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

module.exports = { DEFAULT_OUTPUT, buildMinuteSnapshot, appendMinuteSnapshot };
