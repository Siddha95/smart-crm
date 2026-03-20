<script setup lang="ts">
interface Comment {
  id: number
  user: string
  text: string
  created_at: string
}

const props = defineProps<{ recordId: number }>()

const api = useApi()
const toast = useToast()

const comments = ref<Comment[]>([])
const newText = ref('')
const sending = ref(false)

async function fetchComments() {
  comments.value = await api.get<Comment[]>(`/comments/?record=${props.recordId}`)
}

await fetchComments()

async function send() {
  const text = newText.value.trim()
  if (!text) return
  sending.value = true
  try {
    await api.post('/comments/', { record: props.recordId, text })
    newText.value = ''
    await fetchComments()
  } catch (e: any) {
    toast.add({ title: e.message, color: 'error' })
  } finally {
    sending.value = false
  }
}

async function remove(id: number) {
  await api.del(`/comments/${id}/`)
  await fetchComments()
}
</script>

<template>
  <div class="space-y-4">
    <div v-if="comments.length === 0" class="text-sm text-gray-400 py-4 text-center">
      Nessun commento.
    </div>

    <div v-for="c in comments" :key="c.id" class="flex gap-3 group">
      <div class="flex-1 bg-gray-50 dark:bg-gray-800 rounded-lg p-3">
        <div class="flex items-center justify-between mb-1">
          <span class="text-xs font-medium text-primary">{{ c.user }}</span>
          <span class="text-xs text-gray-400">{{ new Date(c.created_at).toLocaleString('it-IT') }}</span>
        </div>
        <p class="text-sm whitespace-pre-wrap">{{ c.text }}</p>
      </div>
      <UButton
        size="xs"
        variant="ghost"
        color="error"
        icon="lucide:trash-2"
        class="opacity-0 group-hover:opacity-100 transition-opacity self-start mt-1"
        @click="remove(c.id)"
      />
    </div>

    <div class="flex gap-2 pt-2 border-t">
      <UInput
        v-model="newText"
        placeholder="Aggiungi un commento..."
        class="flex-1"
        @keydown.enter.exact="send"
      />
      <UButton icon="lucide:send" :loading="sending" :disabled="!newText.trim()" @click="send" />
    </div>
  </div>
</template>
