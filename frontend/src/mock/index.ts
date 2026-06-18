// 本地 mock 数据：dev-004 接口未上线前用于跑通三页
// 通过 VITE_USE_MOCK 控制是否启用（见 src/api/index.ts）
// 池子选自 PRD/watchlist v1 中的代表性 LOF（10 只精简集，正式联调以后端为准）

import type {
  FundType,
  IngestRealtimeBody,
  IngestRealtimeData,
  LofDetailData,
  LofHistoryData,
  LofListData,
  ListParams
} from '@/api/types'

interface MockMeta {
  code: string
  name: string
  type: FundType
  scale_yi: number
  benchmark_raw: string
  coverage_top10: number
  benchmark_assigned_weight: number
  cash_weight: number
}

const META: MockMeta[] = [
  { code: '161725', name: '招商中证白酒(LOF)A', type: 'index', scale_yi: 300, benchmark_raw: '中证白酒指数收益率×95%+银行活期×5%', coverage_top10: 0.93, benchmark_assigned_weight: 0.95, cash_weight: 0.05 },
  { code: '160706', name: '嘉实美国成长(QDII-LOF)', type: 'index', scale_yi: 18, benchmark_raw: '罗素1000成长指数×95%+人民币活期×5%', coverage_top10: 0.85, benchmark_assigned_weight: 0.95, cash_weight: 0.05 },
  { code: '501050', name: '华夏中证500指数(LOF)A', type: 'index', scale_yi: 26, benchmark_raw: '中证500指数×95%+活期×5%', coverage_top10: 0.20, benchmark_assigned_weight: 0.95, cash_weight: 0.05 },
  { code: '160119', name: '南方中证500ETF联接(LOF)', type: 'index', scale_yi: 12, benchmark_raw: '中证500指数×95%+活期×5%', coverage_top10: 0.20, benchmark_assigned_weight: 0.95, cash_weight: 0.05 },
  { code: '160222', name: '国泰国证食品饮料(LOF)', type: 'industry', scale_yi: 8, benchmark_raw: '国证食品饮料指数×95%+活期×5%', coverage_top10: 0.78, benchmark_assigned_weight: 0.95, cash_weight: 0.05 },
  { code: '160630', name: '鹏华医药(LOF)A', type: 'industry', scale_yi: 9, benchmark_raw: '中证医药卫生指数×90%+活期×10%', coverage_top10: 0.71, benchmark_assigned_weight: 0.90, cash_weight: 0.10 },
  { code: '162605', name: '景顺长城鼎益(LOF)', type: 'active', scale_yi: 35, benchmark_raw: '沪深300×80%+中债综合×15%+活期×5%', coverage_top10: 0.55, benchmark_assigned_weight: 0.95, cash_weight: 0.05 },
  { code: '162703', name: '广发小盘成长(LOF)A', type: 'active', scale_yi: 22, benchmark_raw: '中证500×80%+中债综合×15%+活期×5%', coverage_top10: 0.48, benchmark_assigned_weight: 0.95, cash_weight: 0.05 },
  { code: '163406', name: '兴全合润(LOF)', type: 'active', scale_yi: 50, benchmark_raw: '沪深300×75%+中债综合×20%+活期×5%', coverage_top10: 0.52, benchmark_assigned_weight: 0.95, cash_weight: 0.05 },
  { code: '160924', name: '大成行业轮动(LOF)', type: 'active', scale_yi: 5, benchmark_raw: '沪深300×80%+中债综合×15%+活期×5%', coverage_top10: 0.40, benchmark_assigned_weight: 0.95, cash_weight: 0.05 }
]

// 简单伪随机：基于 code + 当前分钟 produce 实时溢价，便于看到 60s 轮询变化
function pseudoRand(seed: string, salt = 0): number {
  let h = 2166136261 ^ salt
  for (let i = 0; i < seed.length; i++) {
    h ^= seed.charCodeAt(i)
    h = Math.imul(h, 16777619)
  }
  return ((h >>> 0) % 10000) / 10000
}

function makeQuote(meta: MockMeta) {
  const minuteSeed = Math.floor(Date.now() / 60000)
  const r1 = pseudoRand(meta.code, minuteSeed)
  const r2 = pseudoRand(meta.code, minuteSeed + 1)
  const iopv = +(0.6 + r1 * 1.6).toFixed(3)
  // 溢价区间 ±6%
  const premium = +((r2 - 0.5) * 0.12).toFixed(4)
  const price = +(iopv * (1 + premium)).toFixed(3)
  // 指数型 PRD §M2 公式 1：直接 ≈ 1.00
  const coverage =
    meta.type === 'index'
      ? 1.0
      : +(meta.coverage_top10 * 0.5 + meta.benchmark_assigned_weight * 0.5).toFixed(2)
  const pctile = +pseudoRand(meta.code, 7).toFixed(2)
  return { price, iopv, premium, coverage, pctile }
}

export function mockListResponse(params: ListParams = {}): LofListData {
  let list = META.slice()
  if (params.type && params.type !== 'all') {
    list = list.filter((m) => m.type === params.type)
  }
  const items = list.map((meta) => {
    const q = makeQuote(meta)
    return {
      code: meta.code,
      name: meta.name,
      type: meta.type,
      price: q.price,
      iopv: q.iopv,
      premium: q.premium,
      coverage: q.coverage,
      pctile_30d: q.pctile,
      source_quality: 'ok' as const
    }
  })

  const sort = params.sort || 'premium_desc'
  if (sort === 'premium_desc') items.sort((a, b) => b.premium - a.premium)
  else if (sort === 'premium_asc') items.sort((a, b) => a.premium - b.premium)
  else if (sort === 'code') items.sort((a, b) => a.code.localeCompare(b.code))

  return { ts: new Date().toISOString(), items }
}

export function mockDetailResponse(code: string): LofDetailData {
  const meta = META.find((m) => m.code === code) || META[0]
  const q = makeQuote(meta)
  return {
    code: meta.code,
    name: meta.name,
    type: meta.type,
    scale_yi: meta.scale_yi,
    coverage_top10: meta.coverage_top10,
    coverage_breakdown: {
      top10_weight: meta.coverage_top10,
      benchmark_assigned_weight: meta.benchmark_assigned_weight,
      cash_weight: meta.cash_weight
    },
    benchmark_raw: meta.benchmark_raw,
    benchmark_components: [
      {
        index_code: meta.type === 'index' ? '399997.SZ' : '000300.SH',
        name: meta.type === 'index' ? '主跟踪指数' : '业绩比较基准主指数',
        weight: meta.benchmark_assigned_weight
      },
      { index_code: 'CASH', name: '银行活期', weight: meta.cash_weight }
    ],
    holdings_top10: [
      { stock_code: '600519.SH', stock_name: '贵州茅台', weight: 0.15 },
      { stock_code: '000858.SZ', stock_name: '五粮液', weight: 0.12 },
      { stock_code: '000568.SZ', stock_name: '泸州老窖', weight: 0.10 },
      { stock_code: '600809.SH', stock_name: '山西汾酒', weight: 0.09 },
      { stock_code: '000596.SZ', stock_name: '古井贡酒', weight: 0.07 },
      { stock_code: '603369.SH', stock_name: '今世缘', weight: 0.06 },
      { stock_code: '000799.SZ', stock_name: '酒鬼酒', weight: 0.06 },
      { stock_code: '603198.SH', stock_name: '迎驾贡酒', weight: 0.05 },
      { stock_code: '600702.SH', stock_name: '舍得酒业', weight: 0.05 },
      { stock_code: '000860.SZ', stock_name: '顺鑫农业', weight: 0.04 }
    ],
    realtime: {
      ts: new Date().toISOString(),
      price: q.price,
      iopv: q.iopv,
      premium: q.premium,
      coverage: q.coverage,
      source_quality: 'ok'
    },
    pctile_30d: q.pctile
  }
}

export function mockHistoryResponse(code: string, days = 30): LofHistoryData {
  const meta = META.find((m) => m.code === code) || META[0]
  const items = []
  const today = new Date()
  for (let i = days - 1; i >= 0; i--) {
    const d = new Date(today)
    d.setDate(d.getDate() - i)
    const day = d.getDay()
    if (day === 0 || day === 6) continue
    const r = pseudoRand(meta.code, i + 100)
    const close = +(0.6 + r * 1.6).toFixed(3)
    const nav = +(close * (1 - (r - 0.5) * 0.06)).toFixed(3)
    const premium = +((close - nav) / nav).toFixed(4)
    items.push({
      date: d.toISOString().slice(0, 10),
      close_price: close,
      official_nav: nav,
      premium_close: premium,
      premium_pctile_30d: +pseudoRand(meta.code, i + 200).toFixed(2)
    })
  }
  return { code: meta.code, granularity: 'day', items }
}

export function mockIngestRealtimeResponse(body: IngestRealtimeBody): IngestRealtimeData {
  const accepted = Array.isArray(body.items) ? body.items.length : 0
  return { accepted, rejected: 0 }
}

export const mockMetaList = META
