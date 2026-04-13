import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig, AxiosResponse } from 'axios'
import { ElNotification } from 'element-plus'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

const httpClient: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

httpClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('auth_token')
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error: AxiosError) => {
    return Promise.reject(error)
  }
)

httpClient.interceptors.response.use(
  (response: AxiosResponse) => {
    return response
  },
  (error: AxiosError) => {
    const message = (error.response?.data as any)?.detail || error.message || '请求失败'
    
    ElNotification({
      title: '请求错误',
      message: message,
      type: 'error',
      duration: 3000
    })
    
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token')
      window.location.href = '/'
    }
    
    return Promise.reject(error)
  }
)

export default httpClient

export const apiEndpoints = {
  health: '/health',
  datasets: '/datasets',
  trainingTasks: '/training/tasks',
  trainedModels: '/models',
  inferenceModels: '/inference/models',
  chatStream: '/inference/chat-stream'
}
