/**
 * HTTP 请求封装
 *
 * 基于 Axios 的简洁封装，提供：
 * - 自动注入 Token
 * - 401 自动跳转登录页
 * - 统一错误提示
 * - 请求超时处理
 */
import axios, { AxiosRequestConfig, InternalAxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/store/modules/user'

const REQUEST_TIMEOUT = 15000

const { VITE_API_URL } = import.meta.env

/** Axios 实例 */
const instance = axios.create({
  timeout: REQUEST_TIMEOUT,
  baseURL: VITE_API_URL,
  headers: { 'Content-Type': 'application/json' }
})

/** 请求拦截器：注入 Token */
instance.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const { accessToken } = useUserStore()
  if (accessToken) {
    config.headers.set('Authorization', `Bearer ${accessToken}`)
  }
  // POST/PUT 时自动序列化 data
  if (config.data && !(config.data instanceof FormData) && !config.headers['Content-Type']) {
    config.headers.set('Content-Type', 'application/json')
    config.data = JSON.stringify(config.data)
  }
  return config
})

/** 401 防抖标记 */
let isLoggingOut = false

/** 响应拦截器：统一错误处理 */
instance.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const status = error.response?.status

    if (status === 401) {
      if (!isLoggingOut) {
        isLoggingOut = true
        ElMessage.error('登录已过期，请重新登录')
        useUserStore().logOut()
        setTimeout(() => { isLoggingOut = false }, 3000)
      }
      return Promise.reject(error)
    }

    // 其他错误统一提示
    const message = error.response?.data?.detail || error.response?.data?.message || '请求失败'
    ElMessage.error(message)
    return Promise.reject(error)
  }
)

/** 扩展请求配置 */
interface RequestConfig extends AxiosRequestConfig {
  /** 是否显示错误消息（默认 true） */
  showError?: boolean
}

/** API 请求方法 */
const request = {
  get<T = any>(config: RequestConfig): Promise<T> {
    return instance.request({ ...config, method: 'GET' })
  },
  post<T = any>(config: RequestConfig): Promise<T> {
    // 自动将 params 转为 data
    if (config.params && !config.data) {
      config.data = config.params
      config.params = undefined
    }
    return instance.request({ ...config, method: 'POST' })
  },
  put<T = any>(config: RequestConfig): Promise<T> {
    if (config.params && !config.data) {
      config.data = config.params
      config.params = undefined
    }
    return instance.request({ ...config, method: 'PUT' })
  },
  del<T = any>(config: RequestConfig): Promise<T> {
    return instance.request({ ...config, method: 'DELETE' })
  }
}

export default request
