// PRD §5.2 / §M2-B.2 active_low_liquidity 低流动性提示（方案 B：前端内置名单，不动 §6 字段）
// 来源：assets/lof-watchlist-v2.csv 中 status=active_low_liquidity 的 13 只代码（watchlist-v2）
// 由 dev-002 维护；如 watchlist-v3 固化后再同步刷新本常量。
export const LOW_LIQUIDITY_CODES: readonly string[] = [
  '501203',
  '501208',
  '501085',
  '501219',
  '501095',
  '501077',
  '501057',
  '501206',
  '501078',
  '501097',
  '501090',
  '501081',
  '501311'
] as const

const LOW_LIQUIDITY_SET = new Set<string>(LOW_LIQUIDITY_CODES)

/** 判定标的是否属于 active_low_liquidity 低流动性候选 */
export function isLowLiquidity(code: string | undefined | null): boolean {
  if (!code) return false
  return LOW_LIQUIDITY_SET.has(String(code))
}

/** 低流动性提示文案（PRD §M2-B.2） */
export const LOW_LIQUIDITY_LABEL = '低流动性，成交额不足，谨慎参考'
