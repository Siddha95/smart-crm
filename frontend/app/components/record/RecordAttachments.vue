<script setup lang="ts">
const props = defineProps<{ recordId: number }>()

const api = useApi()
const toast = useToast()
const config = useRuntimeConfig()

interface Attachment {
  id: number
  file_type: string
  label: string
  filename: string
  file_url: string
  uploaded_at: string
}

const attachments = ref<Attachment[]>([])
const uploading = ref(false)

async function fetch() {
  attachments.value = await api.get<Attachment[]>(`/attachments/?record=${props.recordId}`)
}

await fetch()

async function upload(event: Event, fileType: string) {
  const input = event.target as HTMLInputElement
  if (!input.files?.length) return

  const formData = new FormData()
  formData.append('file', input.files[0])
  formData.append('record', String(props.recordId))
  formData.append('file_type', fileType)

  uploading.value = true
  try {
    await api.upload('/attachments/', formData)
    toast.add({ title: 'File caricato.', color: 'success' })
    await fetch()
  } catch (e: any) {
    toast.add({ title: e.message, color: 'error' })
  } finally {
    uploading.value = false
    input.value = ''
  }
}

async function remove(id: number) {
  await api.del(`/attachments/${id}/`)
  await fetch()
}

const iconMap: Record<string, string> = {
  photo: 'lucide:image',
  pdf: 'lucide:file-text',
  document: 'lucide:file',
  other: 'lucide:paperclip',
}
</script>

<template>
  <div class="space-y-4">
    <div class="flex gap-2">
      <label>
        <UButton as="span" icon="lucide:image" variant="outline" :loading="uploading">
          Carica foto
        </UButton>
        <input type="file" accept="image/*" class="hidden" @change="upload($event, 'photo')" />
      </label>

      <label>
        <UButton as="span" icon="lucide:file-text" variant="outline" :loading="uploading">
          Carica PDF
        </UButton>
        <input type="file" accept="application/pdf" class="hidden" @change="upload($event, 'pdf')" />
      </label>
    </div>

    <div v-if="attachments.length === 0" class="text-sm text-gray-400 py-4 text-center">
      Nessun allegato.
    </div>

    <div v-for="att in attachments" :key="att.id" class="flex items-center gap-3 p-2 rounded hover:bg-gray-50 dark:hover:bg-gray-800">
      <UIcon :name="iconMap[att.file_type] || 'lucide:paperclip'" class="text-xl text-gray-500" />
      <div class="flex-1 min-w-0">
        <p class="text-sm font-medium truncate">{{ att.label || att.filename }}</p>
        <p class="text-xs text-gray-400">{{ new Date(att.uploaded_at).toLocaleDateString('it-IT') }}</p>
      </div>
      <div class="flex gap-1">
        <UButton size="xs" variant="ghost" icon="lucide:eye" :to="att.file_url" target="_blank" />
        <UButton size="xs" variant="ghost" icon="lucide:download" :to="att.file_url" download />
        <UButton size="xs" variant="ghost" icon="lucide:trash-2" color="error" @click="remove(att.id)" />
      </div>
    </div>
  </div>
</template>
