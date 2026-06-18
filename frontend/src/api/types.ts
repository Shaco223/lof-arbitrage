// PRD §5 / §6 字段契约（前后端联调基线）

export type FundType = 'index' | 'industry' | 'active'
export type SourceQuality = 'ok' | 'degraded' | 'stale'
export type AlertDirection = 'premium' | 'discount'

/** 列表项（api-lof-list -> data.items[i]） */
export interface LofListItem {
  code: string
  name: string
  type: FundType
  price: number
  iopv: number
  /** 溢价率，小数；0.0224 = 2.24% */
  premium: number
  /** 估算覆盖率，0~1 */
  coverage: number
  /** 30 天分位，0~1 */
  pctile_30d: number
  source_quality?: SourceQuality
}

/** 列表响应 */
export interface LofListData {
  ts: string
  items: LofListItem[]
}

/** 三段式覆盖率（AC-T1） */
export interface CoverageBreakdown {
  top10_weight: number
  benchmark_assigned_weight: number
  cash_weight: number
}

export interface BenchmarkComponent {
  index_code: string
  name: string
  weight: number
}

export interface HoldingTop {
  stock_code: string
  stock_name: string
  weight: number
}

/** 详情响应 */
export interface LofDetailData {
  code: string
  name: string
  type: FundType
  scale_yi: number
  coverage_top10: number
  coverage_breakdown: CoverageBreakdown
  benchmark_raw: string
  benchmark_components: BenchmarkComponent[]
  holdings_top10: HoldingTop[]
  realtime: {
    ts: string
    price: number
    iopv: number
    premium: number
    coverage: number
    source_quality: SourceQuality
  }
  pctile_30d: number
}

/** 历史项（api-lof-history） */
export interface LofHistoryItem {
  date: string
  close_price: number
  official_nav: number
  premium_close: number
  premium_pctile_30d: number
}

export interface LofHistoryData {
  code: string
  granularity: 'day' | 'minute'
  items: LofHistoryItem[]
}

/** 通用响应 */
export interface ApiResponse<T> {
  code: number
  message: string
  data: T
}

/** 列表请求参数 */
export interface ListParams {
  sort?: 'premium_desc' | 'premium_asc' | 'code'
  type?: 'all' | FundType
}

export interface DetailParams {
  code: string
}

export interface HistoryParams {
  code: string
  days?: number
  granularity?: 'day' | 'minute'
}

export interface IngestRealtimeItem {
  code: string
  price: number
  iopv: number
  premium: number
  coverage: number
  source_quality?: SourceQuality
}

export interface IngestRealtimeBody {
  ts: string
  items: IngestRealtimeItem[]
}

export interface IngestRealtimeData {
  accepted: number
  rejected: number
}

/** 本地监控配置 */
export interface MonitorSettings {
  /** 溢价告警阈值，默认 0.05 */
  premiumThreshold: number
  /** 折价告警阈值（绝对值），默认 0.02 */
  discountThreshold: number
  /** 推送通道：serverchan / email，二选一 */
  channel: 'serverchan' | 'email'
  /** Server酱 SendKey 或邮箱地址（仅本地存储，不上传） */
  channelTarget: string
  /** 列表轮询间隔（毫秒） */
  pollIntervalMs: number
}
