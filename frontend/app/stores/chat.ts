interface Message {
  role: 'user' | 'assistant' | 'error'
  content: string
}

// Chiave speciale per la chat globale (nessun datasource selezionato)
const GLOBAL_KEY = 0

export const useChatStore = defineStore('chat', () => {
  const histories = ref<Record<number, Message[]>>({})
  const open = ref(false)
  const activeDatasourceId = ref<number | null>(null)

  const historyKey = computed(() => activeDatasourceId.value ?? GLOBAL_KEY)
  const messages = computed<Message[]>(() => histories.value[historyKey.value] ?? [])

  function openFor(datasourceId: number) {
    activeDatasourceId.value = datasourceId
    open.value = true
  }

  async function send(question: string) {
    const id = activeDatasourceId.value
    const key = historyKey.value

    if (!histories.value[key]) histories.value[key] = []
    histories.value[key].push({ role: 'user', content: question })

    const config = useRuntimeConfig()
    const authStore = useAuthStore()
    const url = id
      ? `${config.public.aiBase}/ai/datasources/${id}/chat`
      : `${config.public.aiBase}/ai/chat`

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(authStore.token ? { Authorization: `Bearer ${authStore.token}` } : {}),
        },
        body: JSON.stringify({ question }),
      })

      const data = await response.json()
      if (!response.ok) {
        histories.value[key].push({ role: 'error', content: data.detail || 'Errore sconosciuto.' })
        return
      }
      histories.value[key].push({ role: 'assistant', content: data.answer })
    } catch {
      histories.value[key].push({ role: 'error', content: 'Impossibile raggiungere il servizio AI.' })
    }
  }

  return { histories, open, activeDatasourceId, messages, openFor, send }
})
