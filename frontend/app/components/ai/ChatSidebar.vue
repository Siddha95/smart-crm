<script setup lang="ts">
import { marked } from 'marked'

const chatStore = useChatStore()
const dsStore = useDataSourcesStore()
const input = ref('')
const sending = ref(false)
const messagesEl = ref<HTMLElement>()

const quickActions = [
  'Chi chiamo oggi?',
  'Piano settimanale',
  'Partner per zona',
  'Clienti inattivi',
]

const datasourceOptions = computed(() => [
  { label: 'Tutti i datasource', value: null },
  ...dsStore.list.map(ds => ({ label: ds.label || ds.name, value: ds.id })),
])

// Auto-seleziona se c'è un solo datasource
if (dsStore.list.length === 1 && !chatStore.activeDatasourceId) {
  chatStore.openFor(dsStore.list[0].id)
}

const selectedDatasourceId = computed({
  get: () => chatStore.activeDatasourceId,
  set: (id) => {
    chatStore.activeDatasourceId = id ?? null
  },
})

async function send(text?: string) {
  const question = text || input.value.trim()
  if (!question) return

  input.value = ''
  sending.value = true
  try {
    await chatStore.send(question)
    await nextTick()
    messagesEl.value?.scrollTo({ top: messagesEl.value.scrollHeight, behavior: 'smooth' })
  } finally {
    sending.value = false
  }
}
</script>

<template>
  <USlideover v-model:open="chatStore.open" side="right" class="w-96">
    <template #title>AI Assistente</template>

    <template #body>
      <div class="flex flex-col gap-3 p-4">
        <!-- Selettore datasource -->
        <USelect
          v-model="selectedDatasourceId"
          :items="datasourceOptions"
          placeholder="Seleziona un datasource..."
          value-key="value"
          label-key="label"
        />

        <!-- Suggerimenti rapidi -->
        <div class="flex flex-wrap gap-2">
          <UButton
            v-for="action in quickActions"
            :key="action"
            size="xs"
            variant="soft"
            @click="send(action)"
          >
            {{ action }}
          </UButton>
        </div>

        <!-- Messaggi -->
        <div ref="messagesEl" class="space-y-3 py-2">
          <div v-if="chatStore.messages.length === 0 && !chatStore.activeDatasourceId" class="text-center text-gray-400 text-sm pt-4 px-4">
            Scrivi una domanda — cercherò in tutti i tuoi datasource.
          </div>
          <div v-else-if="chatStore.messages.length === 0" class="text-center text-gray-400 text-sm pt-4">
            Fai una domanda sui dati di questo datasource.
          </div>

          <div
            v-for="(msg, i) in chatStore.messages"
            :key="i"
            :class="[
              'p-3 rounded-lg text-sm max-w-[85%]',
              msg.role === 'user'
                ? 'ml-auto bg-primary text-white'
                : msg.role === 'error'
                  ? 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400'
                  : 'bg-gray-100 dark:bg-gray-800 prose prose-sm dark:prose-invert max-w-none'
            ]"
            v-html="msg.role === 'assistant' ? marked.parse(msg.content) : msg.content"
          />

          <div v-if="sending" class="flex gap-1 p-3">
            <span class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0ms" />
            <span class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 150ms" />
            <span class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 300ms" />
          </div>
        </div>
      </div>
    </template>

    <template #footer>
      <div class="flex gap-2 p-4 border-t w-full">
        <UInput
          v-model="input"
          placeholder="Scrivi una domanda..."
          class="flex-1"
          @keydown.enter="send()"
        />
        <UButton icon="lucide:send" :loading="sending" @click="send()" />
      </div>
    </template>
  </USlideover>
</template>
