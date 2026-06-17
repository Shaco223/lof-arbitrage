import axios, { type AxiosInstance, type AxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus'
import type { ApiResponse } from '@/types'

// 统一的 axios 实例：超时 10s，自动剥离 ApiResponse 包装
const instance: AxiosInstance = axios.create({
  baseURL: '/api',
  timeout: 10_000,
  headers: { 'Content-Type': 'application/json' }
})

instance.interceptors.response.use(
  (response) => response,
  (error) => {
    const msg = error?.response?.data?.msg || error?.message || '网络请求失败'
    ElMessage.error(msg)
    return Promise.reject(error)
  }
)

/** 统一请求函数：返回业务 data 字段 */
export async function request<T>(config: AxiosRequestConfig): Promise<T> {
  const resp = await instance.request<ApiResponse<T>>(config)
  const body = resp.data
  if (body && typeof body === 'object' && 'code' in body) {
    if (body.code !== 0) {
      ElMessage.error(body.msg || '接口返回异常')
      throw new Error(body.msg || 'API error')
    }
    return body.data
  }
  // 兼容直接返回数据的接口
  return resp.data as unknown as T
}

export default instance
