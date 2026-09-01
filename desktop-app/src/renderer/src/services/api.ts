const API_BASE_URL = 'http://localhost:8000'
const API_BASE_URL_NORMALIZED = API_BASE_URL.replace(/\/$/, '')

function buildApiUrl(path: string) {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  return `${API_BASE_URL_NORMALIZED}${normalizedPath}`
}

export function getStoredToken() {
  if (typeof window === 'undefined') {
    return null
  }

  return localStorage.getItem('jarvis-access-token')
}

export function getRefreshToken() {
  if (typeof window === 'undefined') {
    return null
  }

  return localStorage.getItem('jarvis-refresh-token')
}

export function persistAuthSession(token: string, user: unknown) {
  if (typeof window === 'undefined') {
    return
  }

  localStorage.setItem('jarvis-access-token', token)
  sessionStorage.setItem('jarvis-auth-user', JSON.stringify(user))
}

export function clearAuthSession() {
  if (typeof window === 'undefined') {
    return
  }

  localStorage.removeItem('jarvis-access-token')
  localStorage.removeItem('jarvis-refresh-token')
  sessionStorage.removeItem('jarvis-auth-user')
}

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
  tokenOverride?: string | null,
): Promise<T> {
  const token = tokenOverride ?? getStoredToken()
  const headers = new Headers(options.headers)

  if (!headers.has('Content-Type') && options.body && typeof options.body === 'string') {
    headers.set('Content-Type', 'application/json')
  }

  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  const response = await fetch(buildApiUrl(path), {
    ...options,
    headers,
  })

  if (!response.ok) {
    const errorBody = await response.text()
    throw new Error(errorBody || `Request failed with status ${response.status}`)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return response.json() as Promise<T>
}
