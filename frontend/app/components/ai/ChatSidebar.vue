<script setup lang="ts">
const chatStore = useChatStore()
const input = ref('')
const sending = ref(false)
const messagesEl = ref<HTMLElement>()

const quickActions = [
  'Chi chiamo oggi?',
  'Piano settimanale',
  'Partner per zona',
  'Clienti inattivi',
]

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

    <div class="flex flex-col h-full p-4 gap-3">
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
      <div ref="messagesEl" class="flex-1 overflow-y-auto space-y-3 py-2">
        <div v-if="chatStore.messages.length === 0" class="text-center text-gray-400 text-sm pt-8">
          Fai una domanda sui tuoi dati.
        </div>

        <div
          v-for="(msg, i) in chatStore.messages"
          :key="i"
          :class="[
            'p-3 rounded-lg text-sm max-w-[85%]',
            msg.role === 'user'
              ? 'ml-auto bg-primary text-white'
              : 'bg-gray-100 dark:bg-gray-800'
          ]"
        >
          {{ msg.content }}
        </div>

        <div v-if="sending" class="flex gap-1 p-3">
          <span class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0ms" />
          <span class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 150ms" />
          <span class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 300ms" />
        </div>
      </div>

      <!-- Input -->
      <div class="flex gap-2 pt-2 border-t">
        <UInput
          v-model="input"
          placeholder="Scrivi una domanda..."
          class="flex-1"
          @keydown.enter="send()"
        />
        <UButton icon="lucide:send" :loading="sending" @click="send()" />
      </div>
    </div>
  </USlideover>
</template>
