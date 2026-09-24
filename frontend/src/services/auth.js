import { api } from './api'

export const authApi = {
  requestAccess: (email) => api.post('/auth/request-access', { email }),
  activate: (token, password) => api.post('/auth/activate', { token, password }),
  login: (email, password) => api.post('/auth/login', { email, password }),
  me: () => api.get('/auth/me'),
}
