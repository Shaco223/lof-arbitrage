'use strict';

const { ok, fail, normalizeQuery } = require('./response');

exports.main = async (event) => {
  const db = uniCloud.database();
  const query = normalizeQuery(event);
  const code = String(query.code || '').trim();
  const days = Math.min(parseInt(query.days || '30', 10), 60);
  const granularity = query.granularity || 'day';

  if (!/^\d{6}$/.test(code) || Number.isNaN(days) || days <= 0 || !['day', 'minute'].includes(granularity)) {
    return fail(4001, '参数缺失或非法');
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

    const historyRes = await db.collection('lof_history').where({ code }).orderBy('date', 'desc').limit(days).get();
    return ok({
      code,
      granularity,
      items: (historyRes.data || []).reverse().map((item) => ({
        date: item.date,
        close_price: item.close_price,
        official_nav: item.official_nav,
        premium_close: item.premium_close,
        premium_pctile_30d: item.premium_pctile_30d
      }))
    });
  } catch (error) {
    console.error(error);
    return fail(5000, '服务异常');
  }
};
