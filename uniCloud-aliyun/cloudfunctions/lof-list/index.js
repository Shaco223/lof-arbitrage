'use strict';

const { ok, fail, normalizeQuery } = require('./response');

const CACHE_TTL_MS = 60 * 1000;
let listCache = null;
let fallbackList = null;

const STATUS_FALLBACK = { active: 'active', active_low_liquidity: 'active_low_liquidity' };
const SUBSCRIBE_DEFAULT = 'unknown';
const REDEEM_DEFAULT = 'unknown';

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
    if (listCache && Date.now() - listCache.createdAt <= CACHE_TTL_MS) {
      return ok(buildResponseFromCache(listCache.payload, sort, fundType));
    }

    const metaWhere = { status: db.command.in(['active', 'active_low_liquidity']) };
    const metaRes = await db.collection('lof_meta').where(metaWhere).limit(100).get();
    const metas = metaRes.data || [];
    const codes = metas.map((item) => item.code);
    if (!codes.length) {
      return ok(buildResponseFromCache(getFallbackList(), sort, fundType));
    }

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
    const items = metas.map((meta) => buildListItem(meta, realtimeByCode[meta.code] || {}, historyByCode[meta.code] || {}));

    const latestTs = Object.values(realtimeByCode).map((item) => item.ts).filter(Boolean).sort().pop() || null;
    if (items.length) listCache = { createdAt: Date.now(), payload: { ts: latestTs, items } };
    return ok(buildResponseFromCache(items.length ? listCache.payload : getFallbackList(), sort, fundType));
  } catch (error) {
    console.error(error);
    return ok(buildResponseFromCache(getFallbackList(), sort, fundType));
  }
};

function buildListItem(meta, rt, hist) {
  const navOfficial = numberOrNull(rt.nav_official);
  const price = numberOrNull(rt.price);
  const iopv = numberOrNull(rt.iopv);
  const premiumNav = computePremiumNav(price, navOfficial);
  // PRD 1.2.1: premium_error is a POST-CLOSE estimate-accuracy metric pre-computed
  // upstream. Prefer the stored value; fall back to live calc only if absent.
  const premiumError = resolvePremiumError(rt.premium_error, iopv, navOfficial);
  return {
    code: meta.code,
    name: meta.name,
    type: meta.type,
    status: STATUS_FALLBACK[meta.status] || 'active',
    price,
    price_change_pct: numberOrNull(rt.price_change_pct),
    volume_amount: numberOrNull(rt.volume_amount),
    iopv,
    premium: numberOrNull(rt.premium),
    nav_official: navOfficial,
    nav_official_date: rt.nav_official_date || null,
    premium_nav: premiumNav,
    premium_error: premiumError,
    coverage: numberOrNull(rt.coverage),
    pctile_30d: numberOrNull(hist.premium_pctile_30d),
    source_quality: rt.source_quality || 'stale',
    subscribe_status: meta.subscribe_status || SUBSCRIBE_DEFAULT,
    redeem_status: meta.redeem_status || REDEEM_DEFAULT,
    fund_scale: numberOrNull(meta.fund_scale != null ? meta.fund_scale : meta.scale_yi),
    circulating_shares: numberOrNull(meta.circulating_shares)
  };
}

function fillListItemDefaults(item) {
  const navOfficial = numberOrNull(item.nav_official);
  const price = numberOrNull(item.price);
  const iopv = numberOrNull(item.iopv);
  const defaults = {
    status: 'active',
    price_change_pct: null,
    volume_amount: null,
    nav_official: navOfficial,
    nav_official_date: null,
    premium_nav: computePremiumNav(price, navOfficial),
    premium_error: resolvePremiumError(item.premium_error, iopv, navOfficial),
    subscribe_status: SUBSCRIBE_DEFAULT,
    redeem_status: REDEEM_DEFAULT,
    fund_scale: null,
    circulating_shares: null
  };
  for (const key of Object.keys(defaults)) {
    if (item[key] === undefined) item[key] = defaults[key];
  }
  return item;
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

function round6(value) {
  return Math.round(value * 1000000) / 1000000;
}

function numberOrNull(value) {
  if (value === null || value === undefined || value === '') return null;
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

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


function buildResponseFromCache(payload, sort, fundType) {
  const items = payload.items
    .filter((item) => fundType === 'all' || item.type === fundType)
    .map((item) => fillListItemDefaults({ ...item }));
  sortItems(items, sort);
  return { ts: payload.ts, items };
}


function getFallbackList() {
  if (!fallbackList) fallbackList = require('./fallback-list.json');
  return fallbackList;
}