interface Message {
  role: 'user' | 'assistant'
  content: string
}

export const useChatStore = defineStore('chat', () => {
  // Storico in memoria — separato per datasource
  const histories = ref<Record<number, Message[]>>({})
  const open = ref(false)
  const activeDatasourceId = ref<number | null>(null)

  const messages = computed<Message[]>(() =>
    activeDatasourceId.value ? (histories.value[activeDatasourceId.value] ?? []) : []
  )

  function openFor(datasourceId: number) {
    activeDatasourceId.value = datasourceId
    open.value = true
  }

  async function send(question: string) {
    const id = activeDatasourceId.value
    if (!id) return

    if (!histories.value[id]) histories.value[id] = []
    histories.value[id].push({ role: 'user', content: question })

    const config = useRuntimeConfig()
    const response = await fetch(
      `${config.public.aiBase}/ai/datasources/${id}/chat`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
      }
    )

    const data = await response.json()
    histories.value[id].push({ role: 'assistant', content: data.answer })
  }

  return { histories, open, activeDatasourceId, messages, openFor, send }
})
