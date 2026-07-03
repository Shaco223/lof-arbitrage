'use strict';

/**
 * PRD 1.6.1 QDII high 扩至 12 只 + 观察池 5 只 not_supported 场景验证。
 *
 * 通过 explicit minute-snapshot 注入 12 只 high 的 qdii_estimate_* 字段, 验证 lof-list
 * 在 type=qdii 时:
 *   - 12 只 high 全部返回 qdii_estimate_quality=high
 *   - 5 只观察池不论 rt 携带什么值, 后端一律返回 qdii_estimate_quality=not_supported
 *   - 观察池标的 qdii_reference_index_code / qdii_estimate_nav / qdii_estimate_premium 均为 null
 */

const assert = require('assert');
const fs = require('fs');
const os = require('os');
const path = require('path');

const { createLocalApiServer } = require('../local-api-server');

const HIGH_SAMPLES = [
  { code: '510900', ref: 'hkHSCEI', nav_official: 1.0, estimate_nav: 1.0302, price: 1.08, prem: 0.04834 },
  { code: '159920', ref: 'hkHSI', nav_official: 1.2, estimate_nav: 1.22412, price: 1.23, prem: 0.004804 },
  { code: '159941', ref: 'usIXIC', nav_official: 1.45, estimate_nav: 1.508435, price: 1.532, prem: 0.015636 },
  { code: '513500', ref: 'usINX', nav_official: 2.34, estimate_nav: 2.35404, price: 2.41, prem: 0.023826 },
  { code: '161125', ref: 'usINX', nav_official: 3.08, estimate_nav: 3.089984, price: 3.11, prem: 0.006475 },
  { code: '501225', ref: 'usSOXX', nav_official: 3.5887, estimate_nav: 3.386235, price: 3.6, prem: 0.063128 },
  { code: '161126', ref: 'usXLV', nav_official: 1.03, estimate_nav: 1.020615, price: 1.05, prem: 0.028816 },
  { code: '161127', ref: 'usXBI', nav_official: 0.72, estimate_nav: 0.740232, price: 0.75, prem: 0.013196 },
  { code: '161128', ref: 'usXLK', nav_official: 1.55, estimate_nav: 1.512885, price: 1.56, prem: 0.031055 },
  { code: '161130', ref: 'usNDX', nav_official: 2.16, estimate_nav: 2.203416, price: 2.24, prem: 0.016625 },
  { code: '160125', ref: 'hkHSI', nav_official: 0.82, estimate_nav: 0.836334, price: 0.83, prem: -0.007563 },
  { code: '501312', ref: 'usXLK', nav_official: 2.4085, estimate_nav: 2.351159, price: 2.4, prem: 0.020783 },
];

const OBSERVATION_CODES = ['164824', '160140', '162415', '164906', '160644'];

function buildSnapshot() {
  const items = HIGH_SAMPLES.map((s) => ({
    code: s.code,
    price: s.price,
    iopv: null,
    premium: null,
    coverage: 1,
    source_quality: 'ok',
    nav_official: s.nav_official,
    nav_official_date: '2026-07-02',
    qdii_estimate_nav: s.estimate_nav,
    qdii_estimate_premium: s.prem,
    qdii_reference_index_code: s.ref,
    qdii_reference_index_name: `${s.ref} ref`,
    qdii_reference_index_change_pct: 0.001,
    qdii_fx_change_pct: -0.001,
    qdii_estimate_quality: 'high',
    qdii_estimate_source: 'reference_index_estimate',
    qdii_nav_date: '2026-07-02',
  }));
  // 观察池: 即便 rt 尝试写入 quality=high, 后端也应强制 not_supported
  for (const code of OBSERVATION_CODES) {
    items.push({
      code,
      price: 1.0,
      iopv: null,
      premium: null,
      coverage: 1,
      source_quality: 'ok',
      nav_official: 1.0,
      nav_official_date: '2026-07-02',
      qdii_estimate_nav: 999,
      qdii_estimate_premium: 999,
      qdii_reference_index_code: 'MALICIOUS',
      qdii_reference_index_name: 'should be dropped',
      qdii_reference_index_change_pct: 0.5,
      qdii_fx_change_pct: 0.5,
      qdii_estimate_quality: 'high',
      qdii_estimate_source: 'reference_index_estimate',
      qdii_nav_date: '2026-07-02',
    });
  }
  return { ts: '2026-07-03T13:27:00+08:00', items };
}

async function run() {
  const outputDir = fs.mkdtempSync(path.join(os.tmpdir(), 'lof-api-qdii-161-'));
  const snapshotFile = path.join(outputDir, 'local-minute-snapshots-v2.jsonl');
  fs.writeFileSync(snapshotFile, JSON.stringify(buildSnapshot()) + '\n', 'utf8');

  const server = createLocalApiServer({ minuteSnapshotFile: snapshotFile });
  await listen(server);
  const baseUrl = `http://127.0.0.1:${server.address().port}`;

  try {
    const list = await requestJson(`${baseUrl}/lof-list?sort=code&type=qdii`);
    const byCode = new Map(list.data.items.map((row) => [row.code, row]));

    // 1) 12 只 high 全部命中且 quality=high
    for (const s of HIGH_SAMPLES) {
      const row = byCode.get(s.code);
      assert.ok(row, `high ${s.code} missing in /lof-list?type=qdii`);
      assert.strictEqual(row.qdii_estimate_quality, 'high', s.code);
      assert.strictEqual(row.qdii_reference_index_code, s.ref, s.code);
      assert.strictEqual(row.qdii_estimate_nav, s.estimate_nav, s.code);
    }

    // 2) 5 只观察池不带 qdii_estimate_*
    for (const code of OBSERVATION_CODES) {
      const row = byCode.get(code);
      assert.ok(row, `observation ${code} missing in /lof-list?type=qdii`);
      assert.strictEqual(row.qdii_estimate_quality, 'not_supported', code);
      assert.strictEqual(row.qdii_estimate_nav, null, code);
      assert.strictEqual(row.qdii_estimate_premium, null, code);
      assert.strictEqual(row.qdii_reference_index_code, null, code);
      assert.strictEqual(row.qdii_reference_index_name, null, code);
      assert.strictEqual(row.qdii_reference_index_change_pct, null, code);
      assert.strictEqual(row.qdii_fx_change_pct, null, code);
      assert.strictEqual(row.qdii_estimate_source, null, code);
      assert.strictEqual(row.qdii_nav_date, null, code);
    }

    // 3) type=qdii 结果里至少 12 只 high + 5 只 not_supported = 17 只 (dataset 里可能还有其他 qdii, 用 filter 严格计数)
    const highs = list.data.items.filter((r) => r.qdii_estimate_quality === 'high');
    const notSupported = list.data.items.filter((r) => r.qdii_estimate_quality === 'not_supported');
    assert.strictEqual(highs.length, 12, `expected 12 QDII high, got ${highs.length}`);
    assert.strictEqual(notSupported.length, 5, `expected 5 QDII observation not_supported, got ${notSupported.length}`);

    // 4) lof-detail 也必须遵循观察池强制 not_supported
    const detail164906 = await requestJson(`${baseUrl}/lof-detail?code=164906`);
    assert.strictEqual(detail164906.data.qdii_estimate_quality, 'not_supported');
    assert.strictEqual(detail164906.data.qdii_estimate_nav, null);
    assert.strictEqual(detail164906.data.qdii_reference_index_code, null);
    const detail501225 = await requestJson(`${baseUrl}/lof-detail?code=501225`);
    assert.strictEqual(detail501225.data.qdii_estimate_quality, 'high');
    assert.strictEqual(detail501225.data.qdii_reference_index_code, 'usSOXX');

    console.log('PRD 1.6.1 QDII high=12 + observation=5 not_supported test passed');
  } finally {
    await close(server);
  }
}

function listen(server) {
  return new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
}

function close(server) {
  return new Promise((resolve, reject) => server.close((error) => error ? reject(error) : resolve()));
}

async function requestJson(url) {
  const response = await fetch(url);
  assert.strictEqual(response.status, 200);
  return response.json();
}

run().catch((error) => {
  console.error(error);
  process.exit(1);
});