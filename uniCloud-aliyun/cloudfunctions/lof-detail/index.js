'use strict';

const { ok, fail, normalizeQuery } = require('./response');

exports.main = async (event) => {
  const db = uniCloud.database();
  const query = normalizeQuery(event);
  const code = String(query.code || '').trim();
  if (!/^\d{6}$/.test(code)) return fail(4001, '参数缺失或非法');

  try {
    const metaRes = await db.collection('lof_meta').where({ code }).limit(1).get();
    const meta = (metaRes.data || [])[0];
    if (!meta) return fail(4040, '资源不存在');

    const holdingsRes = await db.collection('lof_holdings').where({ code }).orderBy('weight', 'desc').limit(10).get();
    const realtimeRes = await db.collection('lof_realtime').where({ code }).orderBy('ts', 'desc').limit(1).get();
    const historyRes = await db.collection('lof_history').where({ code }).orderBy('date', 'desc').limit(1).get();
    const realtime = (realtimeRes.data || [])[0] || null;
    const latestHistory = (historyRes.data || [])[0] || {};

    return ok({
      code: meta.code,
      name: meta.name,
      type: meta.type,
      scale_yi: meta.scale_yi,
      coverage_top10: meta.coverage_top10,
      coverage_breakdown: meta.coverage_breakdown || { top10_weight: meta.coverage_top10, benchmark_assigned_weight: 0, cash_weight: 0 },
      benchmark_raw: meta.benchmark_raw,
      benchmark_components: meta.benchmark_components || [],
      holdings_top10: (holdingsRes.data || []).map((item) => ({ stock_code: item.stock_code, stock_name: item.stock_name, weight: item.weight })),
      realtime: realtime ? {
        ts: realtime.ts,
        price: realtime.price,
        iopv: realtime.iopv,
        premium: realtime.premium,
        coverage: realtime.coverage,
        source_quality: realtime.source_quality || 'stale'
      } : null,
      pctile_30d: latestHistory.premium_pctile_30d
    });
  } catch (error) {
    console.error(error);
    return fail(5000, '服务异常');
  }
};
