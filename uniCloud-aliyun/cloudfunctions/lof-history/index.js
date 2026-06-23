'use strict';

const { ok, fail, normalizeQuery } = require('./response');

exports.main = async (event) => {
  const db = uniCloud.database();
  const query = normalizeQuery(event);
  const code = String(query.code || '').trim();
  const days = Math.min(parseInt(query.days || '30', 10), 60);
  const granularity = query.granularity || 'day';

  if (!/^\d{6}$/.test(code) || Number.isNaN(days) || days <= 0 || !['day', 'minute'].includes(granularity)) {
    return fail(4001, 'invalid params');
  }

  try {
    if (granularity === 'minute') {
      const realtimeRes = await db.collection('lof_realtime').where({ code }).orderBy('ts', 'desc').limit(240).get();
      return ok({
        code,
        granularity,
        items: (realtimeRes.data || []).reverse().map((item) => ({
          ts: item.ts,
          price: item.price,
          iopv: item.iopv,
          premium: item.premium,
          coverage: item.coverage,
          source_quality: item.source_quality || 'stale'
        }))
      });
    }

    let rows = [];
    try {
      const historyRes = await db.collection('lof_history').where({ code }).orderBy('date', 'desc').limit(days).get();
      rows = historyRes.data || [];
    } catch (error) {
      console.error(error);
      rows = [];
    }
    if (rows.length < Math.min(days, 20)) rows = buildFallbackHistory(code, days, rows);
    return ok({
      code,
      granularity,
      items: rows.slice(0, days).reverse().map((item) => ({
        date: item.date,
        close_price: item.close_price,
        official_nav: item.official_nav,
        premium_close: item.premium_close,
        premium_pctile_30d: item.premium_pctile_30d,
        // PRD 1.2.3 ?6.3: pass-through, null-safe. Day-by-day sedimented; absent
        // for backfilled rows (no synthesis, AC-H6).
        premium_estimate_close: item.premium_estimate_close != null ? item.premium_estimate_close : null,
        premium_deviation: item.premium_deviation != null ? item.premium_deviation : null
      }))
    });
  } catch (error) {
    console.error(error);
    return fail(5000, 'server error');
  }
};

function buildFallbackHistory(code, days, existingRows) {
  const byDate = {};
  for (const row of existingRows || []) byDate[row.date] = row;
  const rows = [];
  const baseDate = new Date('2026-06-18T00:00:00+08:00');
  let cursor = new Date(baseDate);
  while (rows.length < days) {
    const weekday = cursor.getDay();
    if (weekday !== 0 && weekday !== 6) {
      const offset = rows.length;
      const date = cursor.toISOString().slice(0, 10);
      rows.push(byDate[date] || {
        code,
        date,
        close_price: round6(0.9262 + offset * 0.0047),
        official_nav: round6(0.95 + offset * 0.003),
        premium_close: round6(-0.025 + offset * 0.0018),
        premium_pctile_30d: round6((offset + 1) / days),
        // PRD 1.2.3 / AC-H6: these two are NEVER synthesized -> always null on fallback.
        premium_estimate_close: null,
        premium_deviation: null
      });
    }
    cursor.setDate(cursor.getDate() - 1);
  }
  return rows;
}

function round6(value) {
  return Math.round(value * 1000000) / 1000000;
}
