// 统一请求层
// - 默认走 uni.request 调 uniCloud URL 化云函数（VITE_API_BASE + /<云函数名>）
// - 当 VITE_USE_MOCK=true（默认）时直接返回本地 mock，确保 dev-004 接口未上线时三页可跑通
// - 全部走 PRD §6 通用响应包装：{ code, message, data }

import type {
  ApiResponse,
  DetailParams,
  HistoryParams,
  IngestRealtimeBody,
  IngestRealtimeData,
  ListParams,
  LofDetailData,
  LofHistoryData,
  LofListData
} from './types'
import {
  mockDetailResponse,
  mockHistoryResponse,
  mockIngestRealtimeResponse,
  mockListResponse
} from '@/mock'

const useMock = (): boolean =>
  String(import.meta.env.VITE_USE_MOCK).toLowerCase() === 'true'

const apiBase = (): string =>
  (import.meta.env.VITE_API_BASE || '').replace(/\/+$/, '')

interface RawRequest {
  /** 云函数名，例如 api-lof-list */
  fn: string
  method?: 'GET' | 'POST'
  query?: Record<string, string | number | undefined>
  body?: Record<string, unknown>
  header?: Record<string, string>
}

function buildUrl({ fn, query }: { fn: string; query?: RawRequest['query'] }): string {
  const base = apiBase()
  const qs = query
    ? '?' +
      Object.entries(query)
        .filter(([, v]) => v !== undefined && v !== null && v !== '')
        .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`)
        .join('&')
    : ''
  return `${base}/${fn}${qs}`
}

async function rawRequest<T>(opts: RawRequest): Promise<T> {
  const url = buildUrl({ fn: opts.fn, query: opts.query })
  return new Promise<T>((resolve, reject) => {
    uni.request({
      url,
      method: opts.method || 'GET',
      data: opts.body,
      header: { 'Content-Type': 'application/json', ...(opts.header || {}) },
      timeout: 8000,
      success: (res) => {
        const body = res.data as ApiResponse<T>
        if (!body || typeof body !== 'object' || !('code' in body)) {
          reject(new Error('响应结构异常'))
          return
        }
        if (body.code !== 0) {
          uni.showToast({ title: body.message || '接口异常', icon: 'none' })
          reject(new Error(body.message || `code=${body.code}`))
          return
        }
        resolve(body.data)
      },
      fail: (err) => {
        uni.showToast({ title: err?.errMsg || '网络错误', icon: 'none' })
        reject(err)
      }
    })
  })
}

/** GET api-lof-list */
export async function getLofList(params: ListParams = {}): Promise<LofListData> {
  if (useMock()) return mockListResponse(params)
  return rawRequest<LofListData>({
    fn: 'api-lof-list',
    method: 'GET',
    query: { sort: params.sort, type: params.type }
  })
}

/** GET api-lof-detail */
export async function getLofDetail(params: DetailParams): Promise<LofDetailData> {
  if (useMock()) return mockDetailResponse(params.code)
  return rawRequest<LofDetailData>({
    fn: 'api-lof-detail',
    method: 'GET',
    query: { code: params.code }
  })
}

/** GET api-lof-history */
export async function getLofHistory(params: HistoryParams): Promise<LofHistoryData> {
  if (useMock()) return mockHistoryResponse(params.code, params.days)
  return rawRequest<LofHistoryData>({
    fn: 'api-lof-history',
    method: 'GET',
    query: {
      code: params.code,
      days: params.days,
      granularity: params.granularity
    }
  })
}

/** POST ingest-realtime（前端仅提供 mock 契约复刻；真实写入由 dev-004 拉取器调用） */
export async function ingestRealtimeMockOnly(
  body: IngestRealtimeBody,
  token = 'mock-token'
): Promise<IngestRealtimeData> {
  if (useMock()) return mockIngestRealtimeResponse(body)
  return rawRequest<IngestRealtimeData>({
    fn: 'ingest-realtime',
    method: 'POST',
    body: body as unknown as Record<string, unknown>,
    header: { 'X-Ingest-Token': token }
  })
}
