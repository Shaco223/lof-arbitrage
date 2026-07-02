// PRD §5 / §6 字段契约（前后端联调基线）
// PRD 1.2 字段对齐升级：新增字段为可选，null/unknown 时前端不渲染（AC-P5）

export type FundType = 'index' | 'industry' | 'active'
export type SourceQuality = 'ok' | 'degraded' | 'stale'
export type AlertDirection = 'premium' | 'discount'
export type QdiiEstimateQuality = 'high' | 'medium' | 'low' | 'unknown'
/** PRD 1.2 subscribe/redeem status: unknown is hidden */
export type SubscribeRedeemStatus = 'open' | 'suspended' | 'limited' | 'closed' | 'unknown'
/** PRD 1.2 LOF status */
export type LofStatus = 'active' | 'active_low_liquidity'
/** PRD 1.6 QDII estimate fields */
export interface QdiiEstimateFields {
  /** Reference-index estimated NAV, not ordinary LOF IOPV */
  qdii_estimate_nav?: number | null
  /** Reference-index estimated premium, not ordinary LOF premium */
  qdii_estimate_premium?: number | null
  qdii_reference_index_code?: string | null
  qdii_reference_index_name?: string | null
  qdii_reference_index_change_pct?: number | null
  qdii_fx_change_pct?: number | null
  qdii_estimate_quality?: QdiiEstimateQuality | null
  qdii_estimate_source?: string | null
  qdii_nav_date?: string | null
}

/** List item (api-lof-list -> data.items[i]) */
export interface LofListItem extends QdiiEstimateFields {
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
  // === PRD 1.2 新增字段（可选；null/unknown 时前端不渲染） ===
  status?: LofStatus
  /** 当日涨跌幅，例 0.0123 = +1.23% */
  price_change_pct?: number | null
  /** 当日成交额，单位"万元" */
  volume_amount?: number | null
  /** 最近披露官方净值 */
  nav_official?: number | null
  /** 净值日期，YYYY-MM-DD */
  nav_official_date?: string | null
  /** 净值溢价 = (price - nav_official) / nav_official */
  premium_nav?: number | null
  /** 估算误差 = iopv - nav_official */
  premium_error?: number | null
  /** 申购状态：open/suspended/limited/closed/unknown */
  subscribe_status?: SubscribeRedeemStatus
  /** 赎回状态：open/suspended/limited/closed/unknown */
  redeem_status?: SubscribeRedeemStatus
  /** PRD 1.3：单期申购限额（元，limited 且非 null 时展示金额） */
  subscribe_limit_amount?: number | null
  /** PRD 1.3：申购限额周期，如 day */
  subscribe_limit_period?: string | null
  /** PRD 1.3：单期赎回限额（元） */
  redeem_limit_amount?: number | null
  /** PRD 1.3：赎回限额周期 */
  redeem_limit_period?: string | null
  /** PRD 1.4：场内份额（万份） */
  shares_onexchange?: number | null
  /** PRD 1.4：当日新增份额（万份） */
  shares_incr_daily?: number | null
  /** PRD 1.4：申购确认日，如 T+1（参考口径，非到账可卖日） */
  purchase_confirm_day?: number | string | null
  /** PRD 1.4：赎回确认日，如 T+1（参考口径，非到账可卖日） */
  redeem_confirm_day?: number | string | null
  /** 基金规模，单位"亿元" */
  fund_scale?: number | null
  /** 场内流通份额，单位"亿份" */
  circulating_shares?: number | null
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
  // === PRD 1.2 新增字段（可选；null 时前端不渲染该列） ===
  /** 个股当日涨跌幅 */
  price_change_pct?: number | null
  /** 个股贡献度 = weight * price_change_pct */
  contribution_pct?: number | null
}

/** 详情响应 */
export interface LofDetailData extends QdiiEstimateFields {
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
    // === PRD 1.2 新增字段（可选） ===
    price_change_pct?: number | null
    volume_amount?: number | null
  }
  pctile_30d: number
  // === PRD 1.2 新增详情字段（可选；null/unknown 时前端不渲染） ===
  status?: LofStatus
  price_change_pct?: number | null
  volume_amount?: number | null
  nav_official?: number | null
  nav_official_date?: string | null
  premium_nav?: number | null
  premium_error?: number | null
  nav_estimate_error_pct?: number | null
  fund_scale?: number | null
  circulating_shares?: number | null
  subscribe_status?: SubscribeRedeemStatus
  redeem_status?: SubscribeRedeemStatus
  /** PRD 1.3：单期申购限额（元，limited 且非 null 时展示金额） */
  subscribe_limit_amount?: number | null
  /** PRD 1.3：申购限额周期，如 day */
  subscribe_limit_period?: string | null
  /** PRD 1.3：单期赎回限额（元） */
  redeem_limit_amount?: number | null
  /** PRD 1.3：赎回限额周期 */
  redeem_limit_period?: string | null
  /** PRD 1.4：场内份额（万份） */
  shares_onexchange?: number | null
  /** PRD 1.4：当日新增份额（万份） */
  shares_incr_daily?: number | null
  /** PRD 1.4：申购确认日，如 T+1（参考口径，非到账可卖日） */
  purchase_confirm_day?: number | string | null
  /** PRD 1.4：赎回确认日，如 T+1（参考口径，非到账可卖日） */
  redeem_confirm_day?: number | string | null
}

/** 历史项（api-lof-history） */
export interface LofHistoryItem {
  date: string
  close_price: number
  official_nav: number
  premium_close: number
  premium_pctile_30d: number
  /** PRD 1.2.3：当日收盘预估溢价（逐日累积不回填，前期为 null） */
  premium_estimate_close?: number | null
  /** PRD 1.2.3：溢价偏差 = 预估溢价 - 收盘溢价 */
  premium_deviation?: number | null
  /** PRD 1.4：当日新增份额（万份，逐日累积不回填，前期为 null） */
  shares_incr_daily?: number | null
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
  type?: 'all' | FundType | 'qdii'
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
