<script setup lang="ts">
const props = defineProps<{
  records: any[]
  stages: string[]
  columns: string[]
}>()

const emit = defineEmits<{
  dropped: [recordId: number, newStage: string, orderedIds: number[]]
  openEdit: [record: any]
}>()

// ── Copia locale mutabile dei gruppi ─────────────────────────────────────────
const groups = ref<Map<string, any[]>>(new Map())

watch(() => props.records, (records) => {
  const map = new Map<string, any[]>([['', []]])
  for (const s of props.stages) map.set(s, [])
  for (const r of records) {
    const key = r.stage && props.stages.includes(r.stage) ? r.stage : ''
    map.get(key)!.push(r)
  }
  groups.value = map
}, { immediate: true })

// ── Drag & drop ───────────────────────────────────────────────────────────────
const draggingId = ref<number | null>(null)
const dragOverStage = ref<string | null>(null)
const dragOverIndex = ref<number | null>(null)

function onDragStart(e: DragEvent, record: any) {
  draggingId.value = record.id
  e.dataTransfer!.effectAllowed = 'move'
}

function onDragOver(e: DragEvent, stage: string, index: number) {
  e.preventDefault()
  e.stopPropagation()
  e.dataTransfer!.dropEffect = 'move'
  dragOverStage.value = stage
  dragOverIndex.value = index
}

function onDrop(stage: string, dropIndex: number) {
  if (draggingId.value === null) return

  // Trova il record e lo stage di origine
  let sourceStage = ''
  let sourceIndex = -1
  for (const [s, recs] of groups.value) {
    const idx = recs.findIndex(r => r.id === draggingId.value)
    if (idx !== -1) { sourceStage = s; sourceIndex = idx; break }
  }
  if (sourceIndex === -1) { draggingId.value = null; return }

  // Rimuovi dalla sorgente
  const sourceGroup = [...groups.value.get(sourceStage)!]
  const [record] = sourceGroup.splice(sourceIndex, 1)
  record.stage = stage

  // Inserisci nella destinazione
  let targetGroup: any[]
  if (sourceStage === stage) {
    targetGroup = sourceGroup
    const adj = dropIndex > sourceIndex ? dropIndex - 1 : dropIndex
    targetGroup.splice(Math.max(0, adj), 0, record)
  } else {
    targetGroup = [...groups.value.get(stage)!]
    targetGroup.splice(dropIndex, 0, record)
  }

  const newGroups = new Map(groups.value)
  newGroups.set(sourceStage, sourceGroup)
  newGroups.set(stage, targetGroup)
  groups.value = newGroups

  // Emetti la lista ordinata piatta di tutti gli id
  const orderedIds: number[] = []
  for (const recs of newGroups.values()) {
    for (const r of recs) orderedIds.push(r.id)
  }

  emit('dropped', draggingId.value, stage, orderedIds)
  draggingId.value = null
  dragOverStage.value = null
  dragOverIndex.value = null
}

function onDragEnd() {
  draggingId.value = null
  dragOverStage.value = null
  dragOverIndex.value = null
}

// ── Card ──────────────────────────────────────────────────────────────────────
const CARD_COLS = 3
const previewCols = computed(() => props.columns.slice(0, CARD_COLS))

function cardTitle(record: any) {
  for (const col of props.columns) {
    const val = record.data[col]
    if (val !== null && val !== undefined && val !== '') return String(val)
  }
  return `#${record.id}`
}
</script>

<template>
  <div class="flex gap-4 overflow-x-auto pb-4 items-start">
    <div
      v-for="stage in ['', ...stages]"
      :key="stage"
      class="flex-shrink-0 w-72 flex flex-col gap-2"
    >
      <!-- Header colonna -->
      <div
        class="flex items-center justify-between px-3 py-2 rounded-lg font-medium text-sm"
        :class="stage ? 'bg-primary/10 text-primary' : 'bg-gray-100 dark:bg-gray-800 text-gray-500'"
      >
        <span>{{ stage || 'Senza stage' }}</span>
        <UBadge :label="String(groups.get(stage)?.length ?? 0)" variant="soft" size="xs" />
      </div>

      <!-- Drop zone colonna -->
      <div class="flex flex-col min-h-24 rounded-lg p-1 transition-colors">

        <template v-for="(record, idx) in (groups.get(stage) ?? [])" :key="record.id">
          <!-- Linea di inserimento SOPRA questa card -->
          <div
            v-if="dragOverStage === stage && dragOverIndex === idx"
            class="h-1 rounded-full bg-primary mx-1 my-0.5 transition-all"
          />

          <!-- Card -->
          <div
            draggable="true"
            class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg p-3 shadow-sm cursor-grab active:cursor-grabbing hover:shadow-md transition-shadow select-none"
            :class="draggingId === record.id ? 'opacity-40' : ''"
            @dragstart="onDragStart($event, record)"
            @dragend="onDragEnd"
            @dragover="onDragOver($event, stage, idx)"
            @drop.prevent="onDrop(stage, idx)"
            @click="emit('openEdit', record)"
          >
            <p class="font-medium text-sm truncate mb-1">{{ cardTitle(record) }}</p>

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

            <UIcon
              v-if="record.is_favorite"
              name="lucide:star"
              class="text-yellow-400 text-xs mt-1"
            />
          </div>
        </template>

        <!-- Drop zone fondo colonna (append) -->
        <div
          class="flex-1 min-h-12 rounded-lg transition-colors"
          :class="[
            dragOverStage === stage && dragOverIndex === (groups.get(stage)?.length ?? 0)
              ? 'border-t-2 border-primary'
              : '',
            draggingId !== null ? 'cursor-copy' : '',
          ]"
          @dragover="onDragOver($event, stage, groups.get(stage)?.length ?? 0)"
          @drop.prevent="onDrop(stage, groups.get(stage)?.length ?? 0)"
        >
          <div
            v-if="!groups.get(stage)?.length"
            class="text-center text-xs text-gray-300 dark:text-gray-600 py-6"
          >
            Trascina qui
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
