export const useAuthStore = defineStore('auth', () => {
  // useCookie è SSR-safe — funziona sia client che server
  const token = useCookie<string | null>('auth_token', { default: () => null })
  const refreshToken = useCookie<string | null>('auth_refresh', { default: () => null })

  const isAuthenticated = computed(() => !!token.value)

  async function login(username: string, password: string) {
    const config = useRuntimeConfig()
    const response = await fetch(`${config.public.apiBase}/auth/token/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    })

    if (!response.ok) throw new Error('Credenziali non valide.')

    const data = await response.json()
    token.value = data.access
    refreshToken.value = data.refresh
  }

  function logout() {
    token.value = null
    refreshToken.value = null
  }

  return { token, refreshToken, isAuthenticated, login, logout }
})
