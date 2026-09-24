import axios from 'axios'

const ACCESS_TOKEN_KEY = 'adappt_access_token'
const REFRESH_TOKEN_KEY = 'adappt_refresh_token'

export const tokenStorage = {
  getAccess: () => localStorage.getItem(ACCESS_TOKEN_KEY),
  getRefresh: () => localStorage.getItem(REFRESH_TOKEN_KEY),
  set: (access, refresh) => {
    localStorage.setItem(ACCESS_TOKEN_KEY, access)
    localStorage.setItem(REFRESH_TOKEN_KEY, refresh)
  },
  clear: () => {
    localStorage.removeItem(ACCESS_TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
  },
}

export const api = axios.create({ baseURL: '/api' })

api.interceptors.request.use((config) => {
  const token = tokenStorage.getAccess()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

let refreshPromise = null

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const { config, response } = error
    if (response?.status !== 401 || config._retried || config.url?.includes('/auth/')) {
      throw error
    }

    config._retried = true
    const refreshToken = tokenStorage.getRefresh()
    if (!refreshToken) {
      tokenStorage.clear()
      throw error
    }

    try {
      refreshPromise =
        refreshPromise ||
        axios.post('/api/auth/refresh', { refresh_token: refreshToken }).finally(() => {
          refreshPromise = null
        })
      const { data } = await refreshPromise
      tokenStorage.set(data.access_token, data.refresh_token)
      config.headers.Authorization = `Bearer ${data.access_token}`
      return api.request(config)
    } catch (refreshError) {
      tokenStorage.clear()
      window.location.href = '/login'
      throw refreshError
    }
  }
)

export function getErrorMessage(error, fallback = 'Something went wrong. Please try again.') {
  return error?.response?.data?.detail || fallback
}
