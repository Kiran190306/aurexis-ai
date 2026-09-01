import { createContext, useContext, useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiRequest, clearAuthSession, persistAuthSession, getStoredToken, getRefreshToken } from '../../services/api'

interface User {
  id: number
  email: string
  username: string
  full_name?: string
  avatar_url?: string
  bio?: string
  timezone?: string
  language?: string
  theme?: string
}

interface AuthContextType {
  user: User | null
  token: string | null
  login: (email: string, password: string) => Promise<void>
  register: (email: string, username: string, password: string) => Promise<void>
  logout: () => void
  isLoading: boolean
  refreshToken: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // Fetch current user on mount if token exists
  const { data: currentUser, refetch: refetchUser } = useQuery({
    queryKey: ['user'],
    queryFn: async () => {
      const data = await apiRequest<User>('/api/v1/auth/me')
      return data
    },
    enabled: !!getStoredToken(),
    retry: false,
  })

  useEffect(() => {
    const storedToken = getStoredToken()
    const storedUser = window.sessionStorage.getItem('jarvis-auth-user')

    if (storedToken) {
      setToken(storedToken)
      if (storedUser) {
        setUser(JSON.parse(storedUser))
      }
    }
    setIsLoading(false)
  }, [])

  // Update user when query data changes
  useEffect(() => {
    if (currentUser) {
      setUser(currentUser)
      sessionStorage.setItem('jarvis-auth-user', JSON.stringify(currentUser))
    }
  }, [currentUser])

  const login = async (email: string, password: string) => {
    const data = await apiRequest<{ access_token: string; refresh_token: string }>('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    })

    setToken(data.access_token)
    localStorage.setItem('jarvis-access-token', data.access_token)
    localStorage.setItem('jarvis-refresh-token', data.refresh_token)
    
    // Fetch user after login
    await refetchUser()
  }

  const register = async (email: string, username: string, password: string) => {
    const data = await apiRequest<User>('/api/v1/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, username, password }),
    })

    setUser(data)
  }

  const logout = async () => {
    try {
      await apiRequest('/api/v1/auth/logout', { method: 'POST' })
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      setUser(null)
      setToken(null)
      clearAuthSession()
    }
  }

  const refreshToken = async () => {
    const refreshTokenValue = getRefreshToken()
    if (!refreshTokenValue) {
      throw new Error('No refresh token available')
    }

    try {
      const data = await apiRequest<{ access_token: string; refresh_token: string }>('/api/v1/auth/refresh', {
        method: 'POST',
        body: JSON.stringify({ refresh_token: refreshTokenValue }),
      })

      setToken(data.access_token)
      localStorage.setItem('jarvis-access-token', data.access_token)
      localStorage.setItem('jarvis-refresh-token', data.refresh_token)
      
      await refetchUser()
    } catch (error) {
      console.error('Token refresh failed:', error)
      logout()
      throw error
    }
  }

  return (
    <AuthContext.Provider value={{ user, token, login, register, logout, isLoading, refreshToken }}>
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
