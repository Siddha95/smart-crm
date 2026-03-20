export const useApi = () => {
  const config = useRuntimeConfig()
  const authStore = useAuthStore()

  // Rinnova l'access token usando il refresh token
  async function refreshAccessToken(): Promise<boolean> {
    if (!authStore.refreshToken) return false
    try {
      const res = await fetch(`${config.public.apiBase}/auth/token/refresh/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh: authStore.refreshToken }),
      })
      if (!res.ok) return false
      const data = await res.json()
      authStore.token = data.access
      if (data.refresh) authStore.refreshToken = data.refresh
      return true
    } catch {
      return false
    }
  }

  const request = async <T>(path: string, options: RequestInit = {}, isRetry = false): Promise<T> => {
    const url = `${config.public.apiBase}${path}`

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string> || {}),
    }

    if (authStore.token) {
      headers['Authorization'] = `Bearer ${authStore.token}`
    }

    const response = await fetch(url, { ...options, headers })

    // Token scaduto — prova il refresh automatico (una sola volta)
    if (response.status === 401 && !isRetry) {
      const refreshed = await refreshAccessToken()
      if (refreshed) return request<T>(path, options, true)
      authStore.logout()
      navigateTo('/login')
      throw new Error('Sessione scaduta.')
    }

    if (response.status === 401) {
      authStore.logout()
      navigateTo('/login')
      throw new Error('Sessione scaduta.')
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Errore sconosciuto.' }))
      throw new Error(error.detail || 'Errore nella richiesta.')
    }

    // 204 No Content (es. DELETE) — nessun body da parsare
    if (response.status === 204) return undefined as T

    return response.json()
  }

  const get = <T>(path: string) => request<T>(path)

  const post = <T>(path: string, body: unknown) =>
    request<T>(path, { method: 'POST', body: JSON.stringify(body) })

  const patch = <T>(path: string, body: unknown) =>
    request<T>(path, { method: 'PATCH', body: JSON.stringify(body) })

  const del = (path: string) => request(path, { method: 'DELETE' })

  const download = async (path: string, filename: string) => {
    const url = `${config.public.apiBase}${path}`
    const res = await fetch(url, {
      headers: authStore.token ? { Authorization: `Bearer ${authStore.token}` } : {},
    })
    if (!res.ok) throw new Error('Download fallito.')
    const blob = await res.blob()
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = filename
    a.click()
    URL.revokeObjectURL(a.href)
  }

  const upload = async <T>(path: string, formData: FormData): Promise<T> => {
    const url = `${config.public.apiBase}${path}`
    const res = await fetch(url, {
      method: 'POST',
      headers: authStore.token ? { Authorization: `Bearer ${authStore.token}` } : {},
      body: formData,
    })
    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: 'Errore nel caricamento.' }))
      throw new Error(error.detail || 'Errore nel caricamento.')
    }
    if (res.status === 204) return undefined as T
    return res.json()
  }

  return { get, post, patch, del, upload, download }
}
