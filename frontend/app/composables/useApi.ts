export const useApi = () => {
  const config = useRuntimeConfig()
  const authStore = useAuthStore()

  const request = async <T>(path: string, options: RequestInit = {}): Promise<T> => {
    const url = `${config.public.apiBase}${path}`

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string> || {}),
    }

    if (authStore.token) {
      headers['Authorization'] = `Bearer ${authStore.token}`
    }

    const response = await fetch(url, { ...options, headers })

    // Token scaduto — logout automatico
    if (response.status === 401) {
      authStore.logout()
      navigateTo('/login')
      throw new Error('Sessione scaduta.')
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Errore sconosciuto.' }))
      throw new Error(error.detail || 'Errore nella richiesta.')
    }

    return response.json()
  }

  const get = <T>(path: string) => request<T>(path)

  const post = <T>(path: string, body: unknown) =>
    request<T>(path, { method: 'POST', body: JSON.stringify(body) })

  const patch = <T>(path: string, body: unknown) =>
    request<T>(path, { method: 'PATCH', body: JSON.stringify(body) })

  const del = (path: string) => request(path, { method: 'DELETE' })

  const upload = <T>(path: string, formData: FormData) => {
    const url = `${config.public.apiBase}${path}`
    return fetch(url, {
      method: 'POST',
      headers: authStore.token ? { Authorization: `Bearer ${authStore.token}` } : {},
      body: formData,
    }).then(r => r.json() as Promise<T>)
  }

  return { get, post, patch, del, upload }
}
