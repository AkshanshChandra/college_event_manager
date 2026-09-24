import { createContext, useCallback, useEffect, useState } from 'react'
import { authApi } from '../services/auth'
import { tokenStorage } from '../services/api'

export const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  const loadMe = useCallback(async () => {
    if (!tokenStorage.getAccess()) {
      setUser(null)
      setLoading(false)
      return
    }
    try {
      const { data } = await authApi.me()
      setUser(data)
    } catch {
      tokenStorage.clear()
      setUser(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadMe()
  }, [loadMe])

  const login = async (email, password) => {
    const { data } = await authApi.login(email, password)
    tokenStorage.set(data.access_token, data.refresh_token)
    await loadMe()
  }

  const activate = async (token, password) => {
    const { data } = await authApi.activate(token, password)
    tokenStorage.set(data.access_token, data.refresh_token)
    await loadMe()
  }

  const logout = () => {
    tokenStorage.clear()
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, activate, logout, refresh: loadMe }}>
      {children}
    </AuthContext.Provider>
  )
}
