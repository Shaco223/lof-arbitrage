'use strict';

const { ok, fail, normalizeQuery } = require('./response');

exports.main = async (event) => {
  const db = uniCloud.database();
  const query = normalizeQuery(event);
  const sort = query.sort || 'premium_desc';
  const fundType = query.type || 'all';

  if (!['premium_desc', 'premium_asc', 'code'].includes(sort)) {
    return fail(4001, 'invalid params');
  }
  if (!['all', 'index', 'industry', 'active'].includes(fundType)) {
    return fail(4001, 'invalid params');
  }

  try {
    const metaWhere = fundType === 'all' ? { status: db.command.in(['active', 'active_low_liquidity']) } : { type: fundType };
    const metaRes = await db.collection('lof_meta').where(metaWhere).limit(100).get();
    const metas = metaRes.data || [];
    const codes = metas.map((item) => item.code);
    if (!codes.length) return ok({ ts: null, items: [] });

    const realtimeRes = await db.collection('lof_realtime')
      .where({ code: db.command.in(codes) })
      .orderBy('ts', 'desc')
      .limit(codes.length * 3)
      .get();
    const historyRes = await db.collection('lof_history')
      .where({ code: db.command.in(codes) })
      .orderBy('date', 'desc')
      .limit(codes.length * 3)
      .get();

    const realtimeByCode = latestByCode(realtimeRes.data || []);
    const historyByCode = latestByCode(historyRes.data || []);
    const items = metas.map((meta) => {
      const rt = realtimeByCode[meta.code] || {};
      const hist = historyByCode[meta.code] || {};
      return {
        code: meta.code,
        name: meta.name,
        type: meta.type,
        price: rt.price,
        iopv: rt.iopv,
        premium: rt.premium,
        coverage: rt.coverage,
        pctile_30d: hist.premium_pctile_30d,
        source_quality: rt.source_quality || 'stale'
      };
    });

    sortItems(items, sort);
    const latestTs = Object.values(realtimeByCode).map((item) => item.ts).filter(Boolean).sort().pop() || null;
    return ok({ ts: latestTs, items });
  } catch (error) {
    console.error(error);
    return fail(5000, 'server error');
  }
};

function latestByCode(rows) {
  const map = {};
  for (const row of rows) {
    if (!map[row.code]) map[row.code] = row;
  }
  return map;
}

function sortItems(items, sort) {
  if (sort === 'premium_asc') items.sort((a, b) => (a.premium || 0) - (b.premium || 0));
  else if (sort === 'code') items.sort((a, b) => a.code.localeCompare(b.code));
  else items.sort((a, b) => (b.premium || 0) - (a.premium || 0));
}
