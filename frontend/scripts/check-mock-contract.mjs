import fs from 'node:fs'
import path from 'node:path'

const mockPath = path.resolve('src/mock/index.ts')
const source = fs.readFileSync(mockPath, 'utf8')
const typeSource = fs.readFileSync(path.resolve('src/api/types.ts'), 'utf8')
const indexSource = fs.readFileSync(path.resolve('src/pages/index/index.vue'), 'utf8')

const requiredExports = [
  'mockListResponse',
  'mockDetailResponse',
  'mockHistoryResponse',
  'mockIngestRealtimeResponse'
]

const requiredFields = {
  list: ['ts', 'items', 'code', 'name', 'type', 'price', 'iopv', 'premium', 'coverage', 'pctile_30d', 'source_quality', 'qdii_estimate_nav', 'qdii_estimate_premium', 'qdii_reference_index_code', 'qdii_reference_index_name', 'qdii_reference_index_change_pct', 'qdii_fx_change_pct', 'qdii_estimate_quality', 'qdii_estimate_source', 'qdii_nav_date'],
  detail: ['coverage_top10', 'coverage_breakdown', 'benchmark_components', 'holdings_top10', 'realtime', 'pctile_30d', 'top10_weight', 'benchmark_assigned_weight', 'cash_weight', 'qdii_estimate_nav', 'qdii_estimate_premium', 'qdii_reference_index_code', 'qdii_reference_index_name', 'qdii_reference_index_change_pct', 'qdii_fx_change_pct', 'qdii_estimate_quality', 'qdii_estimate_source', 'qdii_nav_date'],
  history: ['granularity', 'close_price', 'official_nav', 'premium_close', 'premium_pctile_30d'],
  ingest: ['accepted', 'rejected']
}

const missingExports = requiredExports.filter((name) => !source.includes(`export function ${name}`))
const missingQdiiRouting = []
if (!typeSource.includes("type?: 'all' | FundType | 'qdii'")) missingQdiiRouting.push('types.ListParams.type=qdii')
if (!indexSource.includes("type: activeMarketTab.value === 'qdii' ? 'qdii' : type.value")) missingQdiiRouting.push('index.loadList type=qdii')
const missingFields = Object.entries(requiredFields)
  .flatMap(([group, fields]) => fields.filter((field) => !source.includes(field)).map((field) => `${group}.${field}`))

if (missingExports.length || missingFields.length || missingQdiiRouting.length) {
  console.error('Mock 契约检查失败')
  if (missingExports.length) console.error('缺少导出:', missingExports.join(', '))
  if (missingFields.length) console.error('缺少字段:', missingFields.join(', '))
  process.exit(1)
}

console.log('Mock 契约检查通过：api-lof-list / api-lof-detail / api-lof-history / ingest-realtime 字段齐全')
