import { createContext, useContext, useState, useEffect } from 'react'
import { apiRequest, clearAuthSession, persistAuthSession, getStoredToken } from '../../services/api'

interface User {
  id: number
  email: string
  username: string
  full_name?: string
  avatar_url?: string
}

interface AuthContextType {
  user: User | null
  token: string | null
  login: (email: string, password: string) => Promise<void>
  register: (email: string, username: string, password: string) => Promise<void>
  logout: () => Promise<void>
  isLoading: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const storedToken = getStoredToken()
    const storedUser = window.sessionStorage.getItem('jarvis-auth-user')

    if (storedToken && storedUser) {
      setToken(storedToken)
      setUser(JSON.parse(storedUser))
    }
    setIsLoading(false)
  }, [])

  const login = async (email: string, password: string) => {
    const data = await apiRequest<{ access_token: string; refresh_token: string }>('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    })
    const authenticatedUser = await apiRequest<User>('/api/v1/auth/me', {}, data.access_token)

    setToken(data.access_token)
    setUser(authenticatedUser)
    persistAuthSession(data.access_token, data.refresh_token, authenticatedUser)
  }

  const register = async (email: string, username: string, password: string) => {
    await apiRequest<User>('/api/v1/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, username, password }),
    })

    // Auto-login after registration
    const loginData = await apiRequest<{ access_token: string; refresh_token: string }>('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    })
    const authenticatedUser = await apiRequest<User>('/api/v1/auth/me', {}, loginData.access_token)

    setToken(loginData.access_token)
    setUser(authenticatedUser)
    persistAuthSession(loginData.access_token, loginData.refresh_token, authenticatedUser)
  }

  const logout = async () => {
    try {
      await apiRequest('/api/v1/auth/logout', { method: 'POST' })
    } catch (error) {
      // Ignore logout errors and clear local session
      console.error('Logout error:', error)
    } finally {
      setUser(null)
      setToken(null)
      clearAuthSession()
    }
  }

  return (
    <AuthContext.Provider value={{ user, token, login, register, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
