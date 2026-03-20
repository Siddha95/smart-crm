<script setup lang="ts">
const props = defineProps<{
  record: any
  columns: string[]
}>()

const emit = defineEmits<{
  updated: []
  close: []
}>()

const api = useApi()
const toast = useToast()
const tab = ref('dati')

const form = reactive({ ...props.record.data })
const saving = ref(false)

async function save() {
  saving.value = true
  try {
    await api.patch(`/records/${props.record.id}/`, { data: { ...form } })
    toast.add({ title: 'Record aggiornato.', color: 'success' })
    emit('updated')
  } catch (e: any) {
    toast.add({ title: e.message, color: 'error' })
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="p-4 space-y-4 h-full flex flex-col">
    <UTabs
      :items="[
        { label: 'Dati', value: 'dati' },
        { label: 'Allegati', value: 'allegati' },
        { label: 'Storico', value: 'storico' },
      ]"
      v-model="tab"
    />

    <!-- Dati -->
    <div v-if="tab === 'dati'" class="flex-1 space-y-3 overflow-y-auto">
      <UFormField v-for="col in columns" :key="col" :label="col">
        <UInput v-model="form[col]" />
      </UFormField>
    </div>

    <!-- Allegati -->
    <div v-else-if="tab === 'allegati'" class="flex-1 overflow-y-auto">
      <RecordAttachments :record-id="record.id" />
    </div>

    <!-- Storico -->
    <div v-else-if="tab === 'storico'" class="flex-1 overflow-y-auto">
      <RecordHistory :record-id="record.id" />
    </div>

    <!-- Azioni footer -->
    <div v-if="tab === 'dati'" class="flex gap-2 pt-2 border-t">
      <UButton :loading="saving" @click="save">Salva</UButton>
      <UButton variant="ghost" @click="emit('close')">Annulla</UButton>
    </div>
  </div>
</template>
