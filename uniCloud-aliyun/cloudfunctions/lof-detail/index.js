'use strict';

const { ok, fail, normalizeQuery } = require('./response');

let fallbackDetails = null;

const SUBSCRIBE_DEFAULT = 'unknown';
const REDEEM_DEFAULT = 'unknown';


exports.main = async (event) => {
  const db = uniCloud.database();
  const query = normalizeQuery(event);
  const code = String(query.code || '').trim();
  if (!/^\d{6}$/.test(code)) return fail(4001, 'invalid params');

  try {
    const metaRes = await db.collection('lof_meta').where({ code }).limit(1).get();
    const meta = (metaRes.data || [])[0];
    if (!meta) return fallbackDetail(code);

    const holdingsRes = await db.collection('lof_holdings').where({ code }).orderBy('weight', 'desc').limit(10).get();
    const realtimeRes = await db.collection('lof_realtime').where({ code }).orderBy('ts', 'desc').limit(1).get();
    const historyRes = await db.collection('lof_history').where({ code }).orderBy('date', 'desc').limit(1).get();
    const realtime = (realtimeRes.data || [])[0] || {};
    const latestHistory = (historyRes.data || [])[0] || {};

    const navOfficial = numberOrNull(realtime.nav_official);
    const price = numberOrNull(realtime.price);
    const iopv = numberOrNull(realtime.iopv);
    const premiumNav = computePremiumNav(price, navOfficial);
    // PRD 1.2.1: premium_error / nav_estimate_error_pct are POST-CLOSE estimate-
    // accuracy metrics pre-computed upstream. Prefer stored value; fall back to
    // live calc only if absent.
    const premiumError = resolvePremiumError(realtime.premium_error, iopv, navOfficial);
    const navEstimateErrorPct = (numberOrNull(realtime.nav_estimate_error_pct) != null)
      ? numberOrNull(realtime.nav_estimate_error_pct)
      : computeNavEstimateErrorPct(premiumError, navOfficial);

    const fundScale = numberOrNull(meta.fund_scale != null ? meta.fund_scale : meta.scale_yi);
    const status = meta.status || 'active';
    const qdiiFields = qdiiFieldsFrom(realtime);

    return ok({
      code: meta.code,
      name: meta.name,
      type: meta.type,
      status,
      scale_yi: meta.scale_yi,
      fund_scale: fundScale,
      circulating_shares: numberOrNull(meta.circulating_shares),
      price,
      price_change_pct: numberOrNull(realtime.price_change_pct),
      volume_amount: numberOrNull(realtime.volume_amount),
      iopv,
      premium: numberOrNull(realtime.premium),
      nav_official: navOfficial,
      nav_official_date: realtime.nav_official_date || null,
      premium_nav: premiumNav,
      premium_error: premiumError,
      nav_estimate_error_pct: navEstimateErrorPct,
      coverage: numberOrNull(realtime.coverage),
      pctile_30d: numberOrNull(latestHistory.premium_pctile_30d),
      source_quality: realtime.source_quality || 'stale',
      subscribe_status: meta.subscribe_status || SUBSCRIBE_DEFAULT,
      redeem_status: meta.redeem_status || REDEEM_DEFAULT,
      subscribe_limit_amount: numberOrNull(meta.subscribe_limit_amount),
      subscribe_limit_period: meta.subscribe_limit_period || null,
      ...qdiiFields,
      // PRD 1.4: daily on-exchange shares (万份) + open-end confirm days (T+N参考)
      shares_onexchange: numberOrNull(meta.shares_onexchange),
      shares_incr_daily: numberOrNull(meta.shares_incr_daily),
      purchase_confirm_day: meta.purchase_confirm_day || null,
      redeem_confirm_day: meta.redeem_confirm_day || null,
      coverage_top10: meta.coverage_top10,
      coverage_breakdown: meta.coverage_breakdown || { top10_weight: meta.coverage_top10, benchmark_assigned_weight: 0, cash_weight: 0 },
      benchmark_raw: meta.benchmark_raw,
      benchmark_components: meta.benchmark_components || [],
      holdings_top10: (holdingsRes.data || []).map((item) => buildHolding(item)),
      realtime: realtime && realtime.ts ? {
        ts: realtime.ts,
        price,
        iopv,
        premium: numberOrNull(realtime.premium),
        coverage: numberOrNull(realtime.coverage),
        source_quality: realtime.source_quality || 'stale',
        ...qdiiFields
      } : null
    });
  } catch (error) {
    console.error(error);
    return fallbackDetail(code);
  }
};


function qdiiFieldsFrom(row) {
  return {
    qdii_estimate_nav: numberOrNull(row.qdii_estimate_nav),
    qdii_estimate_premium: numberOrNull(row.qdii_estimate_premium),
    qdii_reference_index_code: row.qdii_reference_index_code || null,
    qdii_reference_index_name: row.qdii_reference_index_name || null,
    qdii_reference_index_change_pct: numberOrNull(row.qdii_reference_index_change_pct),
    qdii_fx_change_pct: numberOrNull(row.qdii_fx_change_pct),
    qdii_estimate_quality: row.qdii_estimate_quality || 'unavailable',
    qdii_estimate_source: row.qdii_estimate_source || null,
    qdii_nav_date: row.qdii_nav_date || null
  };
}

function buildHolding(item) {
  const weight = numberOrNull(item.weight);
  const priceChangePct = numberOrNull(item.price_change_pct);
  let contributionPct = null;
  if (weight != null && priceChangePct != null) {
    contributionPct = round6(weight * priceChangePct);
  }
  return {
    stock_code: item.stock_code,
    stock_name: item.stock_name,
    weight,
    price_change_pct: priceChangePct,
    contribution_pct: contributionPct
  };
}

// Sanity guard: when |premium_nav| exceeds this, price and nav_official are
// almost certainly out of sync (live price vs stale NAV) rather than a real
// arbitrage gap, so we degrade to null instead of showing e.g. +156% to users.
const PREMIUM_NAV_SANITY_LIMIT = 0.5;

function computePremiumNav(price, navOfficial) {
  if (price == null || navOfficial == null || navOfficial <= 0) return null;
  const value = round6((price - navOfficial) / navOfficial);
  if (Math.abs(value) > PREMIUM_NAV_SANITY_LIMIT) return null;
  return value;
}

function computePremiumError(iopv, navOfficial) {
  if (iopv == null || navOfficial == null) return null;
  return round6(iopv - navOfficial);
}

function resolvePremiumError(stored, iopv, navOfficial) {
  const s = numberOrNull(stored);
  if (s != null) return s;
  return computePremiumError(iopv, navOfficial);
}

function computeNavEstimateErrorPct(premiumError, navOfficial) {
  if (premiumError == null || navOfficial == null || navOfficial <= 0) return null;
  return round6(premiumError / navOfficial);
}

function numberOrNull(value) {
  if (value === null || value === undefined || value === '') return null;
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

function round6(value) {
  return Math.round(value * 1000000) / 1000000;
}

function fallbackDetail(code) {
  if (!fallbackDetails) fallbackDetails = require('./fallback-detail.json');
  const detail = fallbackDetails[code];
  if (!detail) return fail(4040, 'not found');
  const qdiiFields = qdiiFieldsFrom(detail);
  return ok({
    ...detail,
    ...qdiiFields,
    realtime: detail.realtime ? { ...detail.realtime, ...qdiiFieldsFrom(detail.realtime) } : detail.realtime
  });
}
