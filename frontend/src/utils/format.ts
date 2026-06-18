// 通用工具函数

/** 小数转百分比字符串，默认 2 位 */
export function fmtPct(v: number | undefined | null, digits = 2): string {
  if (v === undefined || v === null || Number.isNaN(v)) return '--'
  return (v * 100).toFixed(digits) + '%'
}

/** 数字四舍五入到 N 位 */
export function fmtNum(v: number | undefined | null, digits = 3): string {
  if (v === undefined || v === null || Number.isNaN(v)) return '--'
  return Number(v).toFixed(digits)
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

/** "上次刷新 mm:ss 前"（弱网/超时态） */
export function freshnessLabel(ts: string | number | undefined | null): string {
  if (!ts) return '--'
  const t = typeof ts === 'string' ? Date.parse(ts) : ts
  if (Number.isNaN(t)) return '--'
  const diff = Math.max(0, Math.floor((Date.now() - t) / 1000))
  const m = Math.floor(diff / 60)
  const s = diff % 60
  return `${m}:${String(s).padStart(2, '0')} 前`
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
