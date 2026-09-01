const API_BASE_URL = (import.meta as ImportMeta & { env?: { VITE_API_URL?: string } }).env?.VITE_API_URL || ''
const API_BASE_URL_NORMALIZED = API_BASE_URL.replace(/\/$/, '')

function buildApiUrl(path: string) {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  return `${API_BASE_URL_NORMALIZED}${normalizedPath}`
}

export function getStoredToken() {
  if (typeof window === 'undefined') {
    return null
  }

  return window.sessionStorage.getItem('jarvis-auth-token')
}

export function persistAuthSession(token: string, user: unknown) {
  if (typeof window === 'undefined') {
    return
  }

  window.sessionStorage.setItem('jarvis-auth-token', token)
  window.sessionStorage.setItem('jarvis-auth-user', JSON.stringify(user))
}

export function clearAuthSession() {
  if (typeof window === 'undefined') {
    return
  }

  window.sessionStorage.removeItem('jarvis-auth-token')
  window.sessionStorage.removeItem('jarvis-auth-user')
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
