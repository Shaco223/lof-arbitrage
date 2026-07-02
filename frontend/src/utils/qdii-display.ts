import type { QdiiEstimateFields } from '@/api/types'

const FUND_NAME_BY_CODE: Record<string, string> = {
  '510900': '易方达恒生国企ETF',
  '159920': '华夏恒生ETF',
  '159941': '广发纳指100ETF',
  '513500': '博时标普500ETF',
  '161125': '易方达标普500LOF'
}

const INDEX_NAME_BY_CODE: Record<string, string> = {
  hkHSCEI: '恒生中国企业指数',
  hkHSI: '恒生指数',
  usIXIC: '纳斯达克综合指数',
  usNDX: '纳斯达克100指数',
  usINX: '标普500指数'
}

function isBrokenText(value?: string | null): boolean {
  if (!value || value === 'unknown') return true
  return value.includes('?') || value.includes('？')
}

export function displayFundName(code: string, name?: string | null): string {
  if (!isBrokenText(name)) return name as string
  return FUND_NAME_BY_CODE[code] || name || '--'
}

export function displayQdiiReferenceIndexName(fields: QdiiEstimateFields): string {
  if (!isBrokenText(fields.qdii_reference_index_name)) return fields.qdii_reference_index_name as string
  const code = fields.qdii_reference_index_code || ''
  return INDEX_NAME_BY_CODE[code] || fields.qdii_reference_index_name || '--'
}
