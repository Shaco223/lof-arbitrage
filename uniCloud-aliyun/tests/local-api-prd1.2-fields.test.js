"use strict";

const assert = require("assert");
const { createLocalApiServer, DEFAULT_TOKEN } = require("../local-api-server");

const LIST_REQUIRED_FIELDS = [
  "code",
  "name",
  "type",
  "status",
  "price",
  "price_change_pct",
  "volume_amount",
  "iopv",
  "premium",
  "nav_official",
  "nav_official_date",
  "premium_nav",
  "premium_error",
  "coverage",
  "pctile_30d",
  "source_quality",
  "subscribe_status",
  "redeem_status",
  "fund_scale",
  "circulating_shares"
];

const DETAIL_REQUIRED_FIELDS = LIST_REQUIRED_FIELDS.concat([
  "coverage_breakdown",
  "benchmark_raw",
  "benchmark_components",
  "scale_yi",
  "holdings_top10",
  "realtime",
  "nav_estimate_error_pct"
]);

async function run() {
  const server = createLocalApiServer({ token: DEFAULT_TOKEN });
  await listen(server);
  const baseUrl = `http://127.0.0.1:${server.address().port}`;

  try {
    const list = await requestJson(`${baseUrl}/lof-list?sort=code`);
    assert.strictEqual(list.code, 0);
    assert.ok(list.data.items.length >= 122, `expected >=122, got ${list.data.items.length}`);
    for (const field of LIST_REQUIRED_FIELDS) {
      assert.ok(field in list.data.items[0], `list[0] missing field ${field}`);
    }

    const detail = await requestJson(`${baseUrl}/lof-detail?code=${list.data.items[0].code}`);
    assert.strictEqual(detail.code, 0);
    for (const field of DETAIL_REQUIRED_FIELDS) {
      assert.ok(field in detail.data, `detail missing field ${field}`);
    }
    assert.ok(Array.isArray(detail.data.holdings_top10));
    if (detail.data.holdings_top10.length > 0) {
      const h = detail.data.holdings_top10[0];
      for (const field of ["stock_code", "stock_name", "weight", "price_change_pct", "contribution_pct"]) {
        assert.ok(field in h, `holdings_top10[0] missing field ${field}`);
      }
    }

    console.log("prd1.2 fields smoke passed");
  } finally {
    await close(server);
  }
}

function listen(server) {
  return new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
}

function close(server) {
  return new Promise((resolve, reject) => server.close((error) => (error ? reject(error) : resolve())));
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, {
    method: options.method || "GET",
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    body: options.body
  });
  assert.strictEqual(response.status, 200);
  return response.json();
}

run().catch((error) => {
  console.error(error);
  process.exit(1);
});
