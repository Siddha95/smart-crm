<script setup lang="ts">
const props = defineProps<{
  records: any[]
  stages: string[]
  columns: string[]
}>()

const emit = defineEmits<{
  stageChanged: [recordId: number, newStage: string]
  openEdit: [record: any]
}>()

// Raggruppa i record per stage
const grouped = computed(() => {
  const map = new Map<string, any[]>([['', []]])
  for (const s of props.stages) map.set(s, [])
  for (const r of props.records) {
    const key = r.stage && props.stages.includes(r.stage) ? r.stage : ''
    map.get(key)!.push(r)
  }
  return map
})

// ── Drag & drop ─────────────────────────────────────────────────────────────
const draggingId = ref<number | null>(null)
const dragOverStage = ref<string | null>(null)

function onDragStart(e: DragEvent, record: any) {
  draggingId.value = record.id
  e.dataTransfer!.effectAllowed = 'move'
}

function onDragOver(e: DragEvent, stage: string) {
  e.preventDefault()
  e.dataTransfer!.dropEffect = 'move'
  dragOverStage.value = stage
}

function onDrop(stage: string) {
  if (draggingId.value === null) return
  const record = props.records.find(r => r.id === draggingId.value)
  if (record && record.stage !== stage) {
    emit('stageChanged', draggingId.value, stage)
  }
  draggingId.value = null
  dragOverStage.value = null
}

function onDragEnd() {
  draggingId.value = null
  dragOverStage.value = null
}

// Preview: prime N colonne visibili sulla card
const CARD_COLS = 3
const previewCols = computed(() => props.columns.slice(0, CARD_COLS))

function cardTitle(record: any) {
  const firstCol = props.columns[0]
  return firstCol ? (record.data[firstCol] ?? `#${record.id}`) : `#${record.id}`
}
</script>

<template>
  <div class="flex gap-4 overflow-x-auto pb-4 items-start">
    <!-- Colonna per ogni stage + colonna "Senza stage" -->
    <div
      v-for="stage in ['', ...stages]"
      :key="stage"
      class="flex-shrink-0 w-72 flex flex-col gap-2"
      @dragover="onDragOver($event, stage)"
      @dragleave="dragOverStage = null"
      @drop.prevent="onDrop(stage)"
    >
      <!-- Header colonna -->
      <div
        class="flex items-center justify-between px-3 py-2 rounded-lg font-medium text-sm"
        :class="stage ? 'bg-primary/10 text-primary' : 'bg-gray-100 dark:bg-gray-800 text-gray-500'"
      >
        <span>{{ stage || 'Senza stage' }}</span>
        <UBadge :label="String(grouped.get(stage)?.length ?? 0)" variant="soft" size="xs" />
      </div>

      <!-- Drop zone -->
      <div
        class="flex flex-col gap-2 min-h-24 rounded-lg p-1 transition-colors"
        :class="dragOverStage === stage ? 'bg-primary/5 ring-2 ring-primary/30' : ''"
      >
        <div
          v-for="record in grouped.get(stage)"
          :key="record.id"
          draggable="true"
          class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg p-3 shadow-sm cursor-grab active:cursor-grabbing hover:shadow-md transition-shadow select-none"
          :class="draggingId === record.id ? 'opacity-40' : ''"
          @dragstart="onDragStart($event, record)"
          @dragend="onDragEnd"
          @click="emit('openEdit', record)"
        >
          <!-- Titolo (prima colonna) -->
          <p class="font-medium text-sm truncate mb-1">{{ cardTitle(record) }}</p>

          <!-- Preview altri campi -->
          <div class="space-y-0.5">
            <p
              v-for="col in previewCols.slice(1)"
              :key="col"
              class="text-xs text-gray-500 dark:text-gray-400 truncate"
            >
              <span class="font-medium text-gray-400">{{ col }}:</span>
              {{ record.data[col] ?? '—' }}
            </p>
          </div>

          <!-- Favorito -->
          <UIcon
            v-if="record.is_favorite"
            name="lucide:star"
            class="text-yellow-400 text-xs mt-1"
          />
        </div>

        <!-- Placeholder drop zone vuota -->
        <div
          v-if="!grouped.get(stage)?.length"
          class="text-center text-xs text-gray-300 dark:text-gray-600 py-6"
        >
          Trascina qui
        </div>
      </div>
    </div>
  </div>
</template>
