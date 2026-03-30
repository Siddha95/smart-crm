<script setup lang="ts">
const props = defineProps<{
  open: boolean
  lat: number
  lng: number
}>()

const emit = defineEmits<{
  'update:open': [value: boolean]
  confirm: [recordId: number, color: string]
}>()

const PIN_COLORS = [
  '#22c55e', // verde
  '#ef4444', // rosso
  '#3b82f6', // blu
  '#f97316', // arancione
  '#a855f7', // viola
]

const dsStore = useDataSourcesStore()
const query = ref('')
const selectedId = ref<number | null>(null)
const selectedColor = ref(PIN_COLORS[0])
const loading = ref(false)

const internalOpen = computed({
  get: () => props.open,
  set: (v) => emit('update:open', v),
})

const filtered = computed(() => {
  const q = query.value.trim().toLowerCase()
  const source = dsStore.allRecords
  if (!q) return source.slice(0, 40)
  return source
    .filter(r => Object.values(r.data).some(v => String(v).toLowerCase().includes(q)))
    .slice(0, 40)
})

watch(() => props.open, async (val) => {
  if (val) {
    if (!dsStore.allRecordsLoaded) {
      loading.value = true
      await dsStore.loadAllRecords()
      loading.value = false
    }
  } else {
    query.value = ''
    selectedId.value = null
    selectedColor.value = PIN_COLORS[0]
  }
})

function confirm() {
  if (!selectedId.value) return
  emit('confirm', selectedId.value, selectedColor.value)
  emit('update:open', false)
}
</script>

<template>
  <UModal v-model:open="internalOpen">
    <template #title>Aggiungi pin alla mappa</template>
    <template #body>
      <div class="space-y-3">
        <p class="text-xs text-gray-400">
          Posizione: {{ lat.toFixed(5) }}, {{ lng.toFixed(5) }}
        </p>
        <UInput v-model="query" icon="lucide:search" placeholder="Cerca record..." autofocus />

        <div class="max-h-72 overflow-y-auto rounded-lg border border-gray-200 dark:border-gray-700">
          <div v-if="loading" class="p-4 text-center text-sm text-gray-400">
            <UIcon name="lucide:loader-circle" class="animate-spin mr-1" /> Caricamento...
          </div>
          <template v-else>
            <button
              v-for="r in filtered"
              :key="r.id"
              class="w-full text-left px-3 py-2.5 border-b border-gray-100 dark:border-gray-800 last:border-0 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
              :class="selectedId === r.id ? 'bg-primary/10 ring-1 ring-inset ring-primary' : ''"
              @click="selectedId = r.id"
            >
              <p class="text-xs text-primary font-medium">{{ r.datasourceLabel }}</p>
              <p class="text-sm truncate text-gray-700 dark:text-gray-300">
                {{ Object.values(r.data).slice(0, 3).join(' · ') }}
              </p>
            </button>
            <div v-if="!filtered.length" class="p-4 text-center text-sm text-gray-400">
              Nessun risultato.
            </div>
          </template>
        </div>
      </div>
    </template>
    <template #footer>
      <div class="flex items-center justify-between w-full gap-4">
        <div class="flex items-center gap-2">
          <span class="text-xs text-gray-400">Colore:</span>
          <button
            v-for="color in PIN_COLORS"
            :key="color"
            class="w-6 h-6 rounded-full border-2 transition-transform hover:scale-110"
            :style="{ backgroundColor: color, borderColor: selectedColor === color ? 'white' : 'transparent' }"
            @click="selectedColor = color"
          />
        </div>
        <div class="flex gap-2">
          <UButton variant="ghost" @click="internalOpen = false">Annulla</UButton>
          <UButton :disabled="!selectedId" icon="lucide:map-pin" @click="confirm">
            Aggiungi pin
          </UButton>
        </div>
      </div>
    </template>
  </UModal>
</template>
