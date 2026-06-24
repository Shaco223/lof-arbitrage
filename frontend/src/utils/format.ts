// 通用工具函数

/** 小数转百分比字符串，默认 2 位 */
export function fmtPct(v: number | undefined | null, digits = 2): string {
  if (v === undefined || v === null || Number.isNaN(v)) return '--'
  return (v * 100).toFixed(digits) + '%'
}

/** 带正负号的百分比，用于涨跌幅 */
export function fmtPctSigned(v: number | undefined | null, digits = 2): string {
  if (v === undefined || v === null || Number.isNaN(v)) return '--'
  const pct = v * 100
  const sign = pct > 0 ? '+' : ''
  return sign + pct.toFixed(digits) + '%'
}

/** 数字四舍五入到 N 位 */
export function fmtNum(v: number | undefined | null, digits = 3): string {
  if (v === undefined || v === null || Number.isNaN(v)) return '--'
  return Number(v).toFixed(digits)
}

/**
 * 成交额展示：源单位"万元"。
 * < 10000 万：直接 x.x 万；>= 10000 万：折算亿
 */
export function fmtVolumeWan(v: number | undefined | null): string {
  if (v === undefined || v === null || Number.isNaN(v)) return '--'
  const num = Number(v)
  if (Math.abs(num) >= 10000) return (num / 10000).toFixed(2) + ' 亿'
  if (Math.abs(num) >= 100) return num.toFixed(0) + ' 万'
  return num.toFixed(1) + ' 万'
}

/** PRD 1.3：申赎限额金额（源单位"元"）转万元口径，如 500000 -> "50万"，2亿 -> "2亿" */
export function fmtLimitAmount(v: number | undefined | null): string {
  if (v === undefined || v === null || Number.isNaN(v)) return ''
  const num = Number(v)
  if (Math.abs(num) >= 1e8) return trimZero(num / 1e8) + '亿'
  if (Math.abs(num) >= 1e4) return trimZero(num / 1e4) + '万'
  return trimZero(num) + '元'
}

function trimZero(n: number): string {
  // 去掉多余小数：50.0 -> "50"，1.5 -> "1.5"
  return Number(n.toFixed(2)).toString()
}

/** 份额（亿份） */
export function fmtSharesYi(v: number | undefined | null): string {
  if (v === undefined || v === null || Number.isNaN(v)) return '--'
  return Number(v).toFixed(2) + ' 亿份'
}

/** PRD §8 覆盖率三档颜色 */
export type CoverageLevel = 'green' | 'yellow' | 'red'

export function coverageLevel(coverage: number): CoverageLevel {
  if (coverage >= 0.9) return 'green'
  if (coverage >= 0.7) return 'yellow'
  return 'red'
}

export function coverageLevelLabel(level: CoverageLevel): string {
  return level === 'green' ? '高置信' : level === 'yellow' ? '可参考' : '不可用'
}

/** 相对时间：短时间显示分钟，长时间显示小时/天，避免 747:34 前这类难读格式。 */
export function freshnessLabel(ts: string | number | undefined | null): string {
  if (!ts) return '--'
  const t = typeof ts === 'string' ? Date.parse(ts) : ts
  if (Number.isNaN(t)) return '--'
  const diff = Math.max(0, Math.floor((Date.now() - t) / 1000))
  if (diff < 60) return '刚刚'
  const m = Math.floor(diff / 60)
  if (m < 60) return `${m} 分钟前`
  const h = Math.floor(m / 60)
  if (h < 24) return `${h} 小时前`
  const d = Math.floor(h / 24)
  return `${d} 天前`
}

/** 交易/接口时间，展示为 YYYY-MM-DD HH:mm:ss，避免长相对时间难以理解。 */
export function fmtDateTime(ts: string | number | undefined | null): string {
  if (!ts) return '--'
  const d = new Date(ts)
  if (Number.isNaN(d.getTime())) return '--'
  const pad = (v: number) => String(v).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

/** 是否在交易时段 09:30-11:30 / 13:00-15:00（周末固定 false） */
export function isMarketOpen(d = new Date()): boolean {
  const day = d.getDay()
  if (day === 0 || day === 6) return false
  const total = d.getHours() * 60 + d.getMinutes()
  const morning = total >= 9 * 60 + 30 && total <= 11 * 60 + 30
  const afternoon = total >= 13 * 60 && total <= 15 * 60
  return morning || afternoon
}

/** 是否为有效数值（非 null / 非 undefined / 非 NaN） */
export function isFiniteNum(v: unknown): v is number {
  return typeof v === 'number' && Number.isFinite(v)
}

/** 字段是否需要渲染：null/undefined/空字符串/'unknown' 一律返回 false（AC-P5） */
export function shouldRender(v: unknown): boolean {
  if (v === null || v === undefined) return false
  if (typeof v === 'string') return v !== '' && v !== 'unknown'
  if (typeof v === 'number') return Number.isFinite(v)
  return true
}
