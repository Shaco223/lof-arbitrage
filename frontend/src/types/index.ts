// 全局类型定义：LOF 基金、行情、套利信号

export type SignalLevel = 'info' | 'warning' | 'strong'
export type ArbitrageDirection = 'premium' | 'discount' | 'flat'

/** LOF 基金基础信息 */
export interface LofFund {
  /** 场内代码，如 161725 */
  code: string
  /** 基金简称 */
  name: string
  /** 基金公司 */
  manager?: string
  /** 跟踪标的或类型，例如 "中证白酒" */
  underlying?: string
  /** 是否启用监控 */
  watching: boolean
}

/** 实时行情快照 */
export interface FundQuote {
  code: string
  name: string
  /** 场内最新价 */
  price: number
  /** 净值估算 */
  iopv: number
  /** 折溢价率，正数为溢价、负数为折价（百分比） */
  premiumRate: number
  /** 当日涨跌幅（百分比） */
  changePct: number
  /** 成交额（元） */
  amount: number
  /** 方向 */
  direction: ArbitrageDirection
  /** 数据更新时间，ISO 字符串 */
  updatedAt: string
}

/** 套利信号 */
export interface ArbitrageSignal {
  id: string
  code: string
  name: string
  level: SignalLevel
  direction: ArbitrageDirection
  premiumRate: number
  /** 预计可套空间（百分比，扣除成本后） */
  expectedProfit: number
  message: string
  triggeredAt: string
}

/** 监控配置 */
export interface MonitorSettings {
  /** 折溢价绝对值阈值（百分比） */
  premiumThreshold: number
  /** 强信号阈值 */
  strongThreshold: number
  /** 刷新间隔（秒） */
  refreshInterval: number
  /** 自动刷新 */
  autoRefresh: boolean
  /** 是否仅展示监控中基金 */
  onlyWatching: boolean
}

/** 通用响应包装 */
export interface ApiResponse<T> {
  code: number
  msg: string
  data: T
}
