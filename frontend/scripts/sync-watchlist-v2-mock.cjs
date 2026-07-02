const fs = require('fs')
const path = require('path')

function parseCsv(text) {
  const lines = text.trim().split(/\r?\n/)
  const parseLine = (line) => {
    const out = []
    let cur = ''
    let quote = false
    for (let i = 0; i < line.length; i++) {
      const ch = line[i]
      if (ch === '"') quote = !quote
      else if (ch === ',' && !quote) { out.push(cur); cur = '' }
      else cur += ch
    }
    out.push(cur)
    return out
  }
  const header = parseLine(lines[0])
  return lines.slice(1).filter(Boolean).map((line) => {
    const cells = parseLine(line)
    return Object.fromEntries(header.map((key, i) => [key, cells[i]]))
  })
}

const watch = parseCsv(fs.readFileSync('assets/lof-watchlist-v2.csv', 'utf8'))
const bench = parseCsv(fs.readFileSync('assets/benchmark-mapping-v2.csv', 'utf8'))
const byCode = new Map()
for (const item of bench) {
  if (!byCode.has(item.code)) byCode.set(item.code, [])
  byCode.get(item.code).push({
    index_code: item.index_code,
    name: item.component_name,
    weight: Number(item.weight)
  })
}

function mapType(type) {
  if (type === '\u6307\u6570') return 'index'
  if (type === '\u884c\u4e1a') return 'industry'
  return 'active'
}

function top10ByType(type, code) {
  if (type === 'index') return code === '161725' ? 0.93 : 0.2
  if (type === 'industry') return 0.72
  return 0.52
}

const metas = watch.map((row) => {
  const type = mapType(row.type)
  const components = byCode.get(row.code) || []
  const assigned = components.filter((item) => item.index_code !== 'CASH').reduce((sum, item) => sum + item.weight, 0)
  const cash = components.filter((item) => item.index_code === 'CASH').reduce((sum, item) => sum + item.weight, 0)
  return {
    code: row.code,
    name: row.name,
    type,
    scale_yi: Number(row.scale_yi),
    benchmark_raw: row.benchmark_raw,
    status: row.status,
    coverage_top10: Number(top10ByType(type, row.code).toFixed(2)),
    benchmark_assigned_weight: Number(assigned.toFixed(2)),
    cash_weight: Number(cash.toFixed(2)),
    benchmark_components: components
  }
})

const tsArray = JSON.stringify(metas, null, 2)
  .replace(/"([^"\\]+)":/g, '$1:')
  .replace(/"(index|industry|active|active_low_liquidity|active)"/g, "'$1'")

const content = `// 本地 mock 数据：dev-004 接口未上线前用于跑通三页
// 默认池已切到 watchlist-v2（30 只，QDII 后置二期），接口返回结构保持 PRD §6。

import type {
  BenchmarkComponent,
  FundType,
  IngestRealtimeBody,
  IngestRealtimeData,
  LofDetailData,
  LofHistoryData,
  LofListData,
  ListParams,
  QdiiEstimateFields
} from '@/api/types'

interface MockMeta {
  code: string
  name: string
  type: FundType
  scale_yi: number
  benchmark_raw: string
  status: 'active' | 'active_low_liquidity'
  coverage_top10: number
  benchmark_assigned_weight: number
  cash_weight: number
  benchmark_components: BenchmarkComponent[]
  qdii?: QdiiEstimateFields
}

const META: MockMeta[] = ${tsArray}


const QDII_HIGH_MOCKS: MockMeta[] = [
  {
    code: '510900',
    name: '易方达恒生国企(QDII-ETF)',
    type: 'index',
    scale_yi: 85,
    benchmark_raw: '恒生中国企业指数收益率（经汇率调整）',
    status: 'active',
    coverage_top10: 1,
    benchmark_assigned_weight: 1,
    cash_weight: 0,
    benchmark_components: [{ index_code: 'HSCEI.HI', name: '恒生中国企业指数', weight: 1 }],
    qdii: {
      qdii_estimate_nav: 1.142,
      qdii_estimate_premium: 0.0321,
      qdii_reference_index_code: 'HSCEI.HI',
      qdii_reference_index_name: '恒生中国企业指数',
      qdii_reference_index_change_pct: 0.0112,
      qdii_fx_change_pct: -0.0018,
      qdii_estimate_quality: 'high',
      qdii_estimate_source: '参考指数+汇率估算',
      qdii_nav_date: '2026-07-01'
    }
  },
  {
    code: '159920',
    name: '华夏恒生ETF(QDII)',
    type: 'index',
    scale_yi: 120,
    benchmark_raw: '恒生指数收益率（经汇率调整）',
    status: 'active',
    coverage_top10: 1,
    benchmark_assigned_weight: 1,
    cash_weight: 0,
    benchmark_components: [{ index_code: 'HSI.HI', name: '恒生指数', weight: 1 }],
    qdii: {
      qdii_estimate_nav: 1.058,
      qdii_estimate_premium: 0.0245,
      qdii_reference_index_code: 'HSI.HI',
      qdii_reference_index_name: '恒生指数',
      qdii_reference_index_change_pct: 0.0096,
      qdii_fx_change_pct: -0.0018,
      qdii_estimate_quality: 'high',
      qdii_estimate_source: '参考指数+汇率估算',
      qdii_nav_date: '2026-07-01'
    }
  },
  {
    code: '159941',
    name: '广发纳指100ETF(QDII)',
    type: 'index',
    scale_yi: 95,
    benchmark_raw: '纳斯达克100指数收益率（经汇率调整）',
    status: 'active',
    coverage_top10: 1,
    benchmark_assigned_weight: 1,
    cash_weight: 0,
    benchmark_components: [{ index_code: 'NDX.GI', name: '纳斯达克100指数', weight: 1 }],
    qdii: {
      qdii_estimate_nav: 1.318,
      qdii_estimate_premium: 0.0418,
      qdii_reference_index_code: 'NDX.GI',
      qdii_reference_index_name: '纳斯达克100指数',
      qdii_reference_index_change_pct: 0.0068,
      qdii_fx_change_pct: 0.0021,
      qdii_estimate_quality: 'high',
      qdii_estimate_source: '参考指数+汇率估算',
      qdii_nav_date: '2026-07-01'
    }
  },
  {
    code: '513500',
    name: '博时标普500ETF(QDII)',
    type: 'index',
    scale_yi: 70,
    benchmark_raw: '标普500指数收益率（经汇率调整）',
    status: 'active',
    coverage_top10: 1,
    benchmark_assigned_weight: 1,
    cash_weight: 0,
    benchmark_components: [{ index_code: 'SPX.GI', name: '标普500指数', weight: 1 }],
    qdii: {
      qdii_estimate_nav: 2.426,
      qdii_estimate_premium: 0.0189,
      qdii_reference_index_code: 'SPX.GI',
      qdii_reference_index_name: '标普500指数',
      qdii_reference_index_change_pct: 0.0042,
      qdii_fx_change_pct: 0.0021,
      qdii_estimate_quality: 'high',
      qdii_estimate_source: '参考指数+汇率估算',
      qdii_nav_date: '2026-07-01'
    }
  },
  {
    code: '161125',
    name: '易方达标普500指数(QDII-LOF)',
    type: 'index',
    scale_yi: 45,
    benchmark_raw: '标普500指数收益率（经汇率调整）',
    status: 'active',
    coverage_top10: 1,
    benchmark_assigned_weight: 1,
    cash_weight: 0,
    benchmark_components: [{ index_code: 'SPX.GI', name: '标普500指数', weight: 1 }],
    qdii: {
      qdii_estimate_nav: null,
      qdii_estimate_premium: null,
      qdii_reference_index_code: 'SPX.GI',
      qdii_reference_index_name: '标普500指数',
      qdii_reference_index_change_pct: null,
      qdii_fx_change_pct: null,
      qdii_estimate_quality: 'high',
      qdii_estimate_source: '参考指数+汇率估算',
      qdii_nav_date: null
    }
  }
]

META.push(...QDII_HIGH_MOCKS)

function pseudoRand(seed: string, salt = 0): number {
  let hash = 2166136261 ^ salt
  for (let index = 0; index < seed.length; index++) {
    hash ^= seed.charCodeAt(index)
    hash = Math.imul(hash, 16777619)
  }
  return ((hash >>> 0) % 10000) / 10000
}

function makeQuote(meta: MockMeta) {
  const minuteSeed = Math.floor(Date.now() / 60000)
  const randomPrice = pseudoRand(meta.code, minuteSeed)
  const randomPremium = pseudoRand(meta.code, minuteSeed + 1)
  const iopv = +(0.6 + randomPrice * 1.6).toFixed(3)
  const premium = +((randomPremium - 0.5) * 0.12).toFixed(4)
  const price = +(iopv * (1 + premium)).toFixed(3)
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
    list = list.filter((meta) => meta.type === params.type)
  }
  const items = list.map((meta) => {
    const quote = makeQuote(meta)
    return {
      code: meta.code,
      name: meta.name,
      type: meta.type,
      price: quote.price,
      iopv: quote.iopv,
      premium: quote.premium,
      coverage: quote.coverage,
      pctile_30d: quote.pctile,
      source_quality: meta.status === 'active_low_liquidity' ? 'degraded' as const : 'ok' as const,
      ...meta.qdii
    }
  })

  const sort = params.sort || 'premium_desc'
  if (sort === 'premium_desc') items.sort((a, b) => b.premium - a.premium)
  else if (sort === 'premium_asc') items.sort((a, b) => a.premium - b.premium)
  else if (sort === 'code') items.sort((a, b) => a.code.localeCompare(b.code))

  return { ts: new Date().toISOString(), items }
}

export function mockDetailResponse(code: string): LofDetailData {
  const meta = META.find((item) => item.code === code) || META[0]
  const quote = makeQuote(meta)
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
    benchmark_components: meta.benchmark_components,
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
      price: quote.price,
      iopv: quote.iopv,
      premium: quote.premium,
      coverage: quote.coverage,
      source_quality: meta.status === 'active_low_liquidity' ? 'degraded' : 'ok'
    },
    pctile_30d: quote.pctile,
    ...meta.qdii
  }
}

export function mockHistoryResponse(code: string, days = 30): LofHistoryData {
  const meta = META.find((item) => item.code === code) || META[0]
  const items = []
  const today = new Date()
  for (let index = days - 1; index >= 0; index--) {
    const date = new Date(today)
    date.setDate(date.getDate() - index)
    const day = date.getDay()
    if (day === 0 || day === 6) continue
    const random = pseudoRand(meta.code, index + 100)
    const close = +(0.6 + random * 1.6).toFixed(3)
    const nav = +(close * (1 - (random - 0.5) * 0.06)).toFixed(3)
    const premium = +((close - nav) / nav).toFixed(4)
    items.push({
      date: date.toISOString().slice(0, 10),
      close_price: close,
      official_nav: nav,
      premium_close: premium,
      premium_pctile_30d: +pseudoRand(meta.code, index + 200).toFixed(2)
    })
  }
  return { code: meta.code, granularity: 'day', items }
}

export function mockIngestRealtimeResponse(body: IngestRealtimeBody): IngestRealtimeData {
  const accepted = Array.isArray(body.items) ? body.items.length : 0
  return { accepted, rejected: 0 }
}

export const mockMetaList = META
`

fs.writeFileSync(path.resolve('frontend/src/mock/index.ts'), content, 'utf8')
console.log(`wrote ${metas.length} mock metas`)
