import axios from 'axios'

// ── URL base ────────────────────────────────────────────────────────────────
// Em produção: defina VITE_API_URL no painel do Netlify/Vercel/Render.
// Em desenvolvimento: usa o proxy local como fallback.
const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

// ── Instância base ──────────────────────────────────────────────────────────
const api = axios.create({
  baseURL: BASE_URL,
  timeout: 15_000,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
})

// ── Helpers de token ────────────────────────────────────────────────────────
const getAccessToken  = () => localStorage.getItem('access_token')
const getRefreshToken = () => localStorage.getItem('refresh_token')
const setTokens = ({ access, refresh }) => {
  localStorage.setItem('access_token',  access)
  localStorage.setItem('refresh_token', refresh)
}
const clearTokens = () => {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
}

// ── Request interceptor: injeta Bearer token ────────────────────────────────
api.interceptors.request.use(
  (config) => {
    const token = getAccessToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error),
)

// ── Response interceptor: refresh automático ───────────────────────────────
let isRefreshing = false
let failedQueue  = []

const processQueue = (error, token = null) => {
  failedQueue.forEach((prom) => {
    if (error) prom.reject(error)
    else prom.resolve(token)
  })
  failedQueue = []
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`
            return api(originalRequest)
          })
          .catch((err) => Promise.reject(err))
      }

      originalRequest._retry = true
      isRefreshing = true

      try {
        const refresh = getRefreshToken()
        const { data } = await axios.post(`${BASE_URL}/accounts/token/refresh/`, { refresh })
        setTokens({ access: data.access, refresh: data.refresh ?? refresh })
        processQueue(null, data.access)
        originalRequest.headers.Authorization = `Bearer ${data.access}`
        return api(originalRequest)
      } catch (refreshError) {
        processQueue(refreshError, null)
        clearTokens()
        window.location.href = '/login'
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    // Normaliza a mensagem de erro para facilitar o uso nos componentes
    const message =
      error.response?.data?.detail ??
      error.response?.data?.message ??
      error.message ??
      'Erro desconhecido. Tente novamente.'

    return Promise.reject({ ...error, friendlyMessage: message })
  },
)

export { setTokens, clearTokens }
export default api
