<script setup lang="ts">
interface Sheet { id: number; label: string }

const props = defineProps<{
  record: any | null          // null = nuovo record
  columns: string[]
  datasourceId: number
  siblingSheets?: Sheet[]
}>()

const emit = defineEmits<{
  saved: []
  deleted: []
  moved: []
  close: []
}>()

const api = useApi()
const toast = useToast()
const tab = ref('dati')

const isNew = computed(() => !props.record?.id)

// Inizializza form dai dati del record (o vuoto per nuovo)
function buildForm() {
  return props.columns.reduce((acc, col) => {
    acc[col] = isNew.value ? '' : (props.record?.data?.[col] ?? '')
    return acc
  }, {} as Record<string, any>)
}

const form = reactive(buildForm())

const saving = ref(false)
const deleting = ref(false)
const confirmDelete = ref(false)
const moveTargetId = ref<number | null>(null)
const moving = ref(false)

async function save() {
  saving.value = true
  try {
    if (isNew.value) {
      await api.post('/records/', { data_source: props.datasourceId, data: { ...form } })
      toast.add({ title: 'Record aggiunto.', color: 'success' })
    } else {
      await api.patch(`/records/${props.record.id}/`, { data: { ...form } })
      toast.add({ title: 'Record aggiornato.', color: 'success' })
    }
    emit('saved')
  } catch (e: any) {
    toast.add({ title: e.message, color: 'error' })
  } finally {
    saving.value = false
  }
}

async function remove() {
  deleting.value = true
  try {
    await api.del(`/records/${props.record.id}/`)
    toast.add({ title: 'Record eliminato.', color: 'success' })
    emit('deleted')
  } catch (e: any) {
    toast.add({ title: e.message, color: 'error' })
  } finally {
    deleting.value = false
    confirmDelete.value = false
  }
}

async function move() {
  if (!moveTargetId.value) return
  moving.value = true
  try {
    await api.patch(`/records/${props.record.id}/move/`, { data_source_id: moveTargetId.value })
    toast.add({ title: 'Record spostato.', color: 'success' })
    emit('moved')
  } catch (e: any) {
    toast.add({ title: e.message, color: 'error' })
  } finally {
    moving.value = false
  }
}

const otherSheets = computed(() =>
  (props.siblingSheets ?? []).filter(s => s.id !== props.datasourceId)
)
</script>

<template>
  <div class="p-4 space-y-4 h-full flex flex-col">
    <!-- Tab solo per record esistenti -->
    <UTabs
      v-if="!isNew"
      :items="[
        { label: 'Dati', value: 'dati' },
        { label: 'Allegati', value: 'allegati' },
        { label: 'Commenti', value: 'commenti' },
        { label: 'Storico', value: 'storico' },
      ]"
      v-model="tab"
    />

    <!-- Form dati -->
    <div v-if="tab === 'dati'" class="flex-1 space-y-3 overflow-y-auto">
      <UFormField v-for="col in columns" :key="col" :label="col">
        <UInput v-model="form[col]" class="w-full" />
      </UFormField>

      <!-- Sposta foglio (solo record esistenti con fogli fratelli) -->
      <template v-if="!isNew && otherSheets.length > 0">
        <div class="pt-3 border-t">
          <p class="text-xs text-gray-400 uppercase tracking-wide font-medium mb-2">Sposta nel foglio</p>
          <div class="flex gap-2">
            <USelect
              v-model="moveTargetId"
              :items="otherSheets.map(s => ({ label: s.label, value: s.id }))"
              placeholder="Seleziona foglio..."
              class="flex-1"
            />
            <UButton
              :loading="moving"
              :disabled="!moveTargetId"
              icon="lucide:arrow-right-left"
              variant="outline"
              @click="move"
            >
              Sposta
            </UButton>
          </div>
        </div>
      </template>
    </div>

    <!-- Allegati -->
    <div v-else-if="tab === 'allegati'" class="flex-1 overflow-y-auto">
      <RecordAttachments :record-id="record.id" />
    </div>

    <!-- Commenti -->
    <div v-else-if="tab === 'commenti'" class="flex-1 overflow-y-auto">
      <RecordComments :record-id="record.id" />
    </div>

    <!-- Storico -->
    <div v-else-if="tab === 'storico'" class="flex-1 overflow-y-auto">
      <RecordHistory :record-id="record.id" />
    </div>

    <!-- Footer -->
    <div v-if="tab === 'dati'" class="flex items-center gap-2 pt-2 border-t">
      <UButton :loading="saving" icon="lucide:save" @click="save">
        {{ isNew ? 'Aggiungi' : 'Salva' }}
      </UButton>
      <UButton variant="ghost" @click="emit('close')">Annulla</UButton>

      <!-- Elimina (solo record esistenti) -->
      <div v-if="!isNew" class="ml-auto">
        <UButton
          v-if="!confirmDelete"
          variant="ghost"
          color="error"
          icon="lucide:trash-2"
          @click="confirmDelete = true"
        />
        <div v-else class="flex items-center gap-2">
          <span class="text-sm text-red-500">Confermi?</span>
          <UButton size="xs" color="error" :loading="deleting" @click="remove">Sì</UButton>
          <UButton size="xs" variant="ghost" @click="confirmDelete = false">No</UButton>
        </div>
      </div>
    </div>
  </div>
</template>
