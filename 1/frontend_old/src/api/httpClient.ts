import axios from 'axios'

const httpClient = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

httpClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

httpClient.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    const message = error.response?.data?.detail || error.message || '请求失败'
    console.error('[httpClient] Error:', message)

    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token')
      window.location.href = '/'
    }

    return Promise.reject(error)
  }
)

export default httpClient
