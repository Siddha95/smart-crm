<script setup lang="ts">
definePageMeta({ middleware: 'auth' })

const route = useRoute()
const router = useRouter()
const api = useApi()
const toast = useToast()
const dsStore = useDataSourcesStore()
const chatStore = useChatStore()

// ─── Datasource corrente ────────────────────────────────────────────────────
const datasourceId = computed(() => Number(route.params.id))
const datasource = computed(() => dsStore.list.find(d => d.id === datasourceId.value))

const siblingSheets = computed(() => {
  const sf = datasource.value?.source_file
  if (!sf) return []
  return dsStore.list.filter(d => d.source_file === sf)
})

// ─── Records ───────────────────────────────────────────────────────────────
const records = ref<any[]>([])
const loading = ref(true)
const total = ref(0)

async function loadRecords() {
  loading.value = true
  try {
    const params = new URLSearchParams()
    params.set('data_source', String(datasourceId.value))
    params.set('page', String(page.value))
    params.set('page_size', '25')
    if (search.value) params.set('search', search.value)
    if (showOnlyFavorites.value) params.set('is_favorite', 'true')
    if (sortCol.value) params.set('ordering', `${sortDesc.value ? '-' : ''}${sortCol.value}`)
    const activeFilters = Object.fromEntries(
      Object.entries(columnFilters.value).filter(([_, v]) => v)
    )
    if (Object.keys(activeFilters).length) params.set('col_filters', JSON.stringify(activeFilters))

    const data = await api.get<{ count: number; results: any[] }>(`/records/?${params}`)
    records.value = data.results
    total.value = data.count
  } catch (e: any) {
    toast.add({ title: e.message, color: 'error' })
  } finally {
    loading.value = false
  }
}

// Simple debounce for search to avoid firing on every keystroke
let searchDebounceTimer: ReturnType<typeof setTimeout> | null = null
function debouncedLoadRecords() {
  if (searchDebounceTimer) clearTimeout(searchDebounceTimer)
  searchDebounceTimer = setTimeout(() => loadRecords(), 350)
}

// ─── Preferiti ─────────────────────────────────────────────────────────────
const showOnlyFavorites = ref(false)

async function toggleFavorite(record: any) {
  try {
    await api.patch(`/records/${record.id}/`, { is_favorite: !record.is_favorite })
    await loadRecords()
  } catch (e: any) {
    toast.add({ title: e.message, color: 'error' })
  }
}

// ─── Filtri colonna ─────────────────────────────────────────────────────────
const showFilters = ref(false)
const columnFilters = ref<Record<string, string>>({})

function clearFilters() {
  columnFilters.value = {}
}

// ─── Ricerca globale ───────────────────────────────────────────────────────
const search = ref('')

// ─── Sorting ───────────────────────────────────────────────────────────────
const sortCol = ref<string | null>(null)
const sortDesc = ref(false)

function toggleSort(col: string) {
  if (sortCol.value !== col) {
    sortCol.value = col
    sortDesc.value = false
  } else if (!sortDesc.value) {
    sortDesc.value = true
  } else {
    sortCol.value = null
    sortDesc.value = false
  }
}

// ─── Paginazione ───────────────────────────────────────────────────────────
const PAGE_SIZE = 25
const page = ref(1)

// Server already returns the right page; map to flat row shape for the table
const pagedRows = computed(() =>
  records.value.map(r => ({ _id: r.id, _favorite: r.is_favorite, ...r.data }))
)

// ─── Colonne visibili ───────────────────────────────────────────────────────
const hiddenColumns = ref<Set<string>>(new Set())

function toggleColumn(col: string) {
  const next = new Set(hiddenColumns.value)
  next.has(col) ? next.delete(col) : next.add(col)
  hiddenColumns.value = next
}

const visibleColumns = computed(() =>
  (datasource.value?.columns ?? []).filter(col => !hiddenColumns.value.has(col))
)

// ─── Larghezza colonne (persistita in localStorage) ─────────────────────────
const storageKey = computed(() => `crm_col_widths_${datasourceId.value}`)

function loadWidths(): Record<string, number> {
  try { return JSON.parse(localStorage.getItem(storageKey.value) || '{}') }
  catch { return {} }
}

// Inizializzato vuoto per evitare hydration mismatch SSR/client.
// I valori da localStorage vengono caricati solo dopo il mount (lato client).
const columnWidths = ref<Record<string, number>>({})

function saveWidths() {
  localStorage.setItem(storageKey.value, JSON.stringify(columnWidths.value))
}

function startResize(col: string, e: MouseEvent) {
  e.preventDefault()
  const startX = e.clientX
  const startW = columnWidths.value[col] ?? 160

  function onMove(ev: MouseEvent) {
    columnWidths.value = { ...columnWidths.value, [col]: Math.max(64, startW + ev.clientX - startX) }
  }
  function onUp() {
    saveWidths()
    window.removeEventListener('mousemove', onMove)
    window.removeEventListener('mouseup', onUp)
  }
  window.addEventListener('mousemove', onMove)
  window.addEventListener('mouseup', onUp)
}

// ─── Selezione multipla ─────────────────────────────────────────────────────
const selectedIds = ref<Set<number>>(new Set())

function toggleSelect(id: number) {
  const next = new Set(selectedIds.value)
  next.has(id) ? next.delete(id) : next.add(id)
  selectedIds.value = next
}

const allPageSelected = computed(() =>
  pagedRows.value.length > 0 && pagedRows.value.every(r => selectedIds.value.has(r._id))
)

function toggleSelectAll() {
  const next = new Set(selectedIds.value)
  if (allPageSelected.value) {
    pagedRows.value.forEach(r => next.delete(r._id))
  } else {
    pagedRows.value.forEach(r => next.add(r._id))
  }
  selectedIds.value = next
}

// ─── Bulk actions ──────────────────────────────────────────────────────────
const bulkMoveTarget = ref<number | null>(null)
const bulkLoading = ref(false)

async function bulkDelete() {
  if (!selectedIds.value.size) return
  bulkLoading.value = true
  try {
    await api.post('/records/bulk_delete/', { ids: [...selectedIds.value] })
    toast.add({ title: `${selectedIds.value.size} record eliminati.`, color: 'success' })
    selectedIds.value = new Set()
    await loadRecords()
  } catch (e: any) {
    toast.add({ title: e.message, color: 'error' })
  } finally {
    bulkLoading.value = false
  }
}

async function bulkMove() {
  if (!selectedIds.value.size || !bulkMoveTarget.value) return
  bulkLoading.value = true
  try {
    await api.post('/records/bulk_move/', { ids: [...selectedIds.value], data_source_id: bulkMoveTarget.value })
    toast.add({ title: `${selectedIds.value.size} record spostati.`, color: 'success' })
    selectedIds.value = new Set()
    bulkMoveTarget.value = null
    await loadRecords()
  } catch (e: any) {
    toast.add({ title: e.message, color: 'error' })
  } finally {
    bulkLoading.value = false
  }
}

// ─── Vista kanban ──────────────────────────────────────────────────────────
const view = ref<'table' | 'kanban'>('table')
const kanbanRecords = ref<any[]>([])
const kanbanLoading = ref(false)

async function loadKanbanRecords() {
  kanbanLoading.value = true
  try {
    const params = new URLSearchParams()
    params.set('data_source', String(datasourceId.value))
    params.set('page_size', '500')
    const data = await api.get<{ count: number; results: any[] }>(`/records/?${params}`)
    kanbanRecords.value = data.results
  } catch (e: any) {
    toast.add({ title: e.message, color: 'error' })
  } finally {
    kanbanLoading.value = false
  }
}

async function onStageChanged(recordId: number, newStage: string) {
  // Ottimistic update
  const r = kanbanRecords.value.find(r => r.id === recordId)
  if (r) r.stage = newStage
  try {
    await api.patch(`/records/${recordId}/`, { stage: newStage })
  } catch (e: any) {
    toast.add({ title: e.message, color: 'error' })
    await loadKanbanRecords()
  }
}

watch(view, (v) => {
  if (v === 'kanban') loadKanbanRecords()
})

// ─── Configurazione stages ──────────────────────────────────────────────────
const stageConfigOpen = ref(false)
const stagesEdit = ref<string[]>([])
const newStageName = ref('')
const savingStages = ref(false)

function openStageConfig() {
  stagesEdit.value = [...(datasource.value?.stages ?? [])]
  newStageName.value = ''
  stageConfigOpen.value = true
}

function addStage() {
  const name = newStageName.value.trim()
  if (!name || stagesEdit.value.includes(name)) return
  stagesEdit.value.push(name)
  newStageName.value = ''
}

function removeStage(i: number) {
  stagesEdit.value.splice(i, 1)
}

async function saveStages() {
  savingStages.value = true
  try {
    await api.patch(`/datasources/${datasourceId.value}/stages/`, { stages: stagesEdit.value })
    await dsStore.fetch()
    stageConfigOpen.value = false
    if (view.value === 'kanban') await loadKanbanRecords()
    toast.add({ title: 'Stage aggiornati.', color: 'success' })
  } catch (e: any) {
    toast.add({ title: e.message, color: 'error' })
  } finally {
    savingStages.value = false
  }
}

// ─── Export ─────────────────────────────────────────────────────────────────
async function exportAs(fmt: 'xlsx' | 'pdf') {
  const name = datasource.value?.name ?? 'export'
  try {
    await api.download(`/datasources/${datasourceId.value}/export/?fmt=${fmt}`, `${name}.${fmt}`)
  } catch (e: any) {
    toast.add({ title: e.message, color: 'error' })
  }
}

// ─── Drawer edit / nuovo ───────────────────────────────────────────────────
const editRecord = ref<any>(null)
const drawerOpen = ref(false)

function openNew() { editRecord.value = null; drawerOpen.value = true }
function openEdit(record: any) { editRecord.value = record; drawerOpen.value = true }
function onSaved() { drawerOpen.value = false; loadRecords() }
function onDeleted() { drawerOpen.value = false; loadRecords() }
function onMoved() { drawerOpen.value = false; loadRecords() }

// ─── Delete da riga ────────────────────────────────────────────────────────
const pendingDelete = ref<any>(null)
const deleteLoading = ref(false)
const deleteModalOpen = computed({
  get: () => !!pendingDelete.value,
  set: (v) => { if (!v) pendingDelete.value = null },
})

async function confirmDelete() {
  if (!pendingDelete.value) return
  deleteLoading.value = true
  try {
    await api.del(`/records/${pendingDelete.value.id}/`)
    toast.add({ title: 'Record eliminato.', color: 'success' })
    pendingDelete.value = null
    loadRecords()
  } catch (e: any) {
    toast.add({ title: e.message, color: 'error' })
  } finally {
    deleteLoading.value = false
  }
}

function getRecord(rowId: number) {
  return records.value.find(r => r.id === rowId)
}

// ─── Cambio foglio ─────────────────────────────────────────────────────────
function switchSheet(id: number) {
  if (id !== datasourceId.value) router.push(`/source/${id}`)
}

// ─── Struttura colonne ──────────────────────────────────────────────────────
const colManagerOpen = ref(false)

async function onColumnsUpdated() {
  await dsStore.fetch()
  await loadRecords()
}

// ─── Watch (dopo tutte le dichiarazioni) ───────────────────────────────────
watch(search, () => {
  page.value = 1
  debouncedLoadRecords()
})
watch([sortCol, sortDesc, showOnlyFavorites, columnFilters], () => {
  page.value = 1
  loadRecords()
}, { deep: true })
watch(showFilters, (v) => { if (!v) { clearFilters() } })
watch(page, loadRecords)
watch(datasourceId, () => {
  page.value = 1
  search.value = ''
  sortCol.value = null
  sortDesc.value = false
  hiddenColumns.value = new Set()
  selectedIds.value = new Set()
  columnFilters.value = {}
  showOnlyFavorites.value = false
  records.value = []
  total.value = 0
  kanbanRecords.value = []
  columnWidths.value = loadWidths()
  if (view.value === 'kanban') loadKanbanRecords()
  else loadRecords()
})

// ─── Init ──────────────────────────────────────────────────────────────────
onMounted(() => { columnWidths.value = loadWidths() })

await dsStore.fetch()
await loadRecords()
</script>

<template>
  <div class="p-6 space-y-4">
    <!-- Toolbar -->
    <div class="flex items-center justify-between gap-3 flex-wrap">
      <div class="flex items-center gap-3">
        <div>
          <h1 class="text-2xl font-semibold">{{ datasource?.source_file ?? datasource?.label }}</h1>
          <p class="text-sm text-gray-500">{{ total }} record</p>
        </div>
        <USelect
          v-if="siblingSheets.length > 1"
          :model-value="datasourceId"
          :items="siblingSheets.map(s => ({ label: s.label, value: s.id }))"
          @update:model-value="switchSheet"
        />
      </div>

      <div class="flex items-center gap-2 flex-wrap">
        <UButton
          :variant="showOnlyFavorites ? 'solid' : 'outline'"
          :color="showOnlyFavorites ? 'warning' : 'neutral'"
          icon="lucide:star"
          size="sm"
          @click="showOnlyFavorites = !showOnlyFavorites"
        />
        <UButton
          :variant="showFilters ? 'solid' : 'outline'"
          icon="lucide:filter"
          size="sm"
          @click="showFilters = !showFilters"
        >Filtri</UButton>
        <UPopover>
          <UButton variant="outline" icon="lucide:columns-3" size="sm">Colonne</UButton>
          <template #content>
            <div class="p-3 space-y-1 min-w-48">
              <p class="text-xs text-gray-400 font-medium uppercase tracking-wide pb-1">Mostra / nascondi</p>
              <label
                v-for="col in datasource?.columns"
                :key="col"
                class="flex items-center gap-2 cursor-pointer py-1 hover:text-primary"
              >
                <input type="checkbox" :checked="!hiddenColumns.has(col)" @change="toggleColumn(col)" />
                <span class="text-sm">{{ col }}</span>
              </label>
            </div>
          </template>
        </UPopover>
        <UButton variant="outline" icon="lucide:settings-2" size="sm" @click="colManagerOpen = true">Struttura</UButton>
        <UDropdownMenu
          :items="[
            [{ label: 'Excel (.xlsx)', icon: 'lucide:table', onSelect: () => exportAs('xlsx') }],
            [{ label: 'PDF', icon: 'lucide:file-text', onSelect: () => exportAs('pdf') }],
          ]"
        >
          <UButton variant="outline" icon="lucide:download" size="sm">Export</UButton>
        </UDropdownMenu>
        <UInput v-model="search" icon="lucide:search" placeholder="Cerca..." class="w-56" size="sm" />
        <!-- Toggle vista -->
        <div class="flex rounded-lg overflow-hidden border border-gray-200 dark:border-gray-700">
          <UButton
            :variant="view === 'table' ? 'solid' : 'ghost'"
            icon="lucide:table"
            size="sm"
            class="rounded-none"
            @click="view = 'table'"
          />
          <UButton
            :variant="view === 'kanban' ? 'solid' : 'ghost'"
            icon="lucide:columns-3"
            size="sm"
            class="rounded-none"
            @click="view = 'kanban'"
          />
        </div>
        <UButton icon="lucide:bot" variant="outline" @click="chatStore.openFor(datasourceId.value)">AI</UButton>
        <UButton icon="lucide:plus" @click="openNew">Aggiungi</UButton>
      </div>
    </div>

    <!-- Filtri colonna -->
    <div v-if="showFilters" class="flex gap-2 flex-wrap items-center bg-gray-50 dark:bg-gray-800 p-3 rounded-lg">
      <div v-for="col in visibleColumns" :key="col" class="flex-1 min-w-32">
        <UInput v-model="columnFilters[col]" :placeholder="col" size="xs" />
      </div>
      <UButton variant="ghost" size="xs" icon="lucide:x" @click="clearFilters" />
    </div>

    <!-- Bulk action bar -->
    <div
      v-if="selectedIds.size > 0"
      class="flex items-center gap-3 bg-primary/5 border border-primary/20 rounded-lg px-4 py-2"
    >
      <span class="text-sm font-medium">{{ selectedIds.size }} selezionati</span>
      <UButton size="xs" color="error" variant="outline" icon="lucide:trash-2" :loading="bulkLoading" @click="bulkDelete">
        Elimina
      </UButton>
      <div v-if="siblingSheets.length > 1" class="flex items-center gap-2">
        <USelect
          v-model="bulkMoveTarget"
          :items="siblingSheets.filter(s => s.id !== datasourceId).map(s => ({ label: s.label, value: s.id }))"
          placeholder="Sposta in..."
          size="xs"
          class="w-40"
        />
        <UButton size="xs" variant="outline" icon="lucide:arrow-right-left" :loading="bulkLoading" :disabled="!bulkMoveTarget" @click="bulkMove">
          Sposta
        </UButton>
      </div>
      <UButton size="xs" variant="ghost" class="ml-auto" @click="selectedIds = new Set()">Deseleziona</UButton>
    </div>

    <!-- Vista Kanban -->
    <div v-if="view === 'kanban'">
      <!-- Header kanban: config stages -->
      <div class="flex items-center justify-between mb-4">
        <p class="text-sm text-gray-500">
          {{ datasource?.stages?.length ? datasource.stages.join(' → ') : 'Nessuno stage configurato' }}
        </p>
        <UButton size="xs" variant="outline" icon="lucide:settings-2" @click="openStageConfig">
          Configura stage
        </UButton>
      </div>

      <div v-if="kanbanLoading" class="flex justify-center py-12">
        <UIcon name="lucide:loader-circle" class="animate-spin text-2xl text-primary" />
      </div>
      <div v-else-if="!datasource?.stages?.length" class="text-center py-12 text-gray-400 text-sm space-y-3">
        <UIcon name="lucide:columns-3" class="text-4xl" />
        <p>Configura gli stage per usare la vista kanban.</p>
        <UButton size="sm" @click="openStageConfig">Configura ora</UButton>
      </div>
      <KanbanBoard
        v-else
        :records="kanbanRecords"
        :stages="datasource.stages"
        :columns="datasource?.columns ?? []"
        @stage-changed="onStageChanged"
        @open-edit="openEdit($event)"
      />
    </div>

    <!-- Tabella con scroll orizzontale e colonne ridimensionabili -->
    <div v-if="view === 'table'" class="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
      <div v-if="loading" class="flex justify-center py-12">
        <UIcon name="lucide:loader-circle" class="animate-spin text-2xl text-primary" />
      </div>
      <table
        v-else
        class="text-sm border-collapse"
        style="table-layout: fixed; min-width: 100%"
      >
        <colgroup>
          <col style="width: 40px" />
          <col
            v-for="col in visibleColumns"
            :key="col"
            :style="{ width: (columnWidths[col] ?? 160) + 'px' }"
          />
          <col style="width: 48px" />
        </colgroup>

        <thead class="bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
          <tr>
            <!-- Select all -->
            <th class="px-3 py-2 text-center">
              <input
                type="checkbox"
                :checked="allPageSelected"
                class="cursor-pointer rounded"
                @change="toggleSelectAll"
              />
            </th>

            <!-- Intestazioni colonne dati -->
            <th
              v-for="col in visibleColumns"
              :key="col"
              class="px-3 py-2 text-left font-medium text-gray-500 relative group select-none"
              style="overflow: hidden"
            >
              <button
                class="flex items-center gap-1 hover:text-primary transition-colors cursor-pointer w-full truncate"
                @click="toggleSort(col)"
              >
                <span class="truncate">{{ col }}</span>
                <span v-if="sortCol === col" class="text-primary text-xs shrink-0">
                  {{ sortDesc ? '↓' : '↑' }}
                </span>
              </button>

              <!-- Resize handle -->
              <div
                class="absolute right-0 top-0 h-full w-1.5 cursor-col-resize hover:bg-primary/40 active:bg-primary transition-colors"
                @mousedown="startResize(col, $event)"
              />
            </th>

            <!-- Colonna azioni -->
            <th class="px-3 py-2" />
          </tr>
        </thead>

        <tbody>
          <tr
            v-if="pagedRows.length === 0"
          >
            <td
              :colspan="visibleColumns.length + 2"
              class="px-3 py-8 text-center text-gray-400 text-sm"
            >
              Nessun record.
            </td>
          </tr>
          <tr
            v-for="(row, i) in pagedRows"
            :key="row._id"
            class="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
            :class="i % 2 === 0 ? '' : 'bg-gray-50/50 dark:bg-gray-800/20'"
          >
            <!-- Checkbox -->
            <td class="px-3 py-2 text-center">
              <input
                type="checkbox"
                :checked="selectedIds.has(row._id)"
                class="cursor-pointer rounded"
                @change="toggleSelect(row._id)"
              />
            </td>

            <!-- Celle dati -->
            <td
              v-for="col in visibleColumns"
              :key="col"
              class="px-3 py-2 text-gray-700 dark:text-gray-300 align-top"
              style="overflow-wrap: break-word; word-break: break-word; overflow: hidden"
            >
              <span v-if="row._favorite && col === visibleColumns[0]" class="inline-flex items-center gap-1">
                <UIcon name="lucide:star" class="text-yellow-400 shrink-0 text-xs" />
                {{ row[col] ?? '—' }}
              </span>
              <template v-else>{{ row[col] ?? '—' }}</template>
            </td>

            <!-- Azioni -->
            <td class="px-3 py-2 text-right" @click.stop>
              <UDropdownMenu
                :items="[
                  [
                    { label: 'Modifica', icon: 'lucide:pencil', onSelect: () => openEdit(getRecord(row._id)) },
                    {
                      label: row._favorite ? 'Rimuovi preferito' : 'Aggiungi preferito',
                      icon: row._favorite ? 'lucide:star-off' : 'lucide:star',
                      onSelect: () => toggleFavorite(getRecord(row._id)),
                    },
                  ],
                  [{ label: 'Elimina', icon: 'lucide:trash-2', color: 'error', onSelect: () => pendingDelete = getRecord(row._id) }],
                ]"
              >
                <UButton size="xs" variant="ghost" icon="lucide:ellipsis-vertical" />
              </UDropdownMenu>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Paginazione (solo tabella) -->
    <div v-if="view === 'table' && total > PAGE_SIZE" class="flex justify-center pt-2">
      <UPagination v-model:page="page" :total="total" :items-per-page="PAGE_SIZE" />
    </div>

    <!-- Modal eliminazione -->
    <UModal v-model:open="deleteModalOpen">
      <template #title>Elimina record</template>
      <template #body>
        <p class="text-sm">Sei sicuro di voler eliminare questo record? L'operazione non è reversibile.</p>
      </template>
      <template #footer>
        <div class="flex gap-2 justify-end">
          <UButton variant="ghost" @click="pendingDelete = null">Annulla</UButton>
          <UButton color="error" :loading="deleteLoading" @click="confirmDelete">Elimina</UButton>
        </div>
      </template>
    </UModal>

    <!-- Modal configurazione stages -->
    <UModal v-model:open="stageConfigOpen">
      <template #title>Configura stage — {{ datasource?.label }}</template>
      <template #body>
        <div class="space-y-4">
          <p class="text-sm text-gray-500">
            Definisci le fasi del pipeline. I record potranno essere spostati tra le colonne nel kanban.
          </p>

          <!-- Lista stage esistenti -->
          <div class="space-y-2">
            <div
              v-for="(stage, i) in stagesEdit"
              :key="i"
              class="flex items-center gap-2 bg-gray-50 dark:bg-gray-800 rounded-lg px-3 py-2"
            >
              <UIcon name="lucide:grip-vertical" class="text-gray-400 cursor-grab" />
              <span class="flex-1 text-sm font-medium">{{ stage }}</span>
              <UButton
                size="xs"
                variant="ghost"
                color="error"
                icon="lucide:x"
                @click="removeStage(i)"
              />
            </div>
            <p v-if="stagesEdit.length === 0" class="text-sm text-gray-400 text-center py-2">
              Nessuno stage. Aggiungine uno sotto.
            </p>
          </div>

          <!-- Aggiungi nuovo stage -->
          <div class="flex gap-2">
            <UInput
              v-model="newStageName"
              placeholder="Nuovo stage (es. Lead, Contattato…)"
              class="flex-1"
              @keydown.enter="addStage"
            />
            <UButton icon="lucide:plus" @click="addStage" :disabled="!newStageName.trim()" />
          </div>

          <!-- Suggerimenti -->
          <div class="flex flex-wrap gap-1">
            <span class="text-xs text-gray-400">Suggerimenti:</span>
            <UButton
              v-for="s in ['Lead', 'Contattato', 'Preventivo', 'Chiuso', 'Perso'].filter(s => !stagesEdit.includes(s))"
              :key="s"
              size="xs"
              variant="soft"
              @click="stagesEdit.push(s)"
            >{{ s }}</UButton>
          </div>
        </div>
      </template>
      <template #footer>
        <div class="flex gap-2 justify-end">
          <UButton variant="ghost" @click="stageConfigOpen = false">Annulla</UButton>
          <UButton :loading="savingStages" @click="saveStages">Salva</UButton>
        </div>
      </template>
    </UModal>

    <!-- Modal struttura colonne -->
    <UModal v-model:open="colManagerOpen">
      <template #title>Struttura colonne</template>
      <template #body>
        <DatasourceColumnManager
          v-if="datasource"
          :datasource-id="datasourceId"
          :columns="datasource.columns"
          @updated="onColumnsUpdated"
        />
      </template>
    </UModal>

    <!-- Drawer modifica / nuovo record -->
    <USlideover v-model:open="drawerOpen">
      <template #title>{{ editRecord ? 'Modifica record' : 'Nuovo record' }}</template>
      <template #body>
        <RecordDetail
          v-if="drawerOpen"
          :key="editRecord?.id ?? 'new'"
          :record="editRecord"
          :columns="datasource?.columns ?? []"
          :datasource-id="datasourceId"
          :sibling-sheets="siblingSheets"
          @saved="onSaved"
          @deleted="onDeleted"
          @moved="onMoved"
          @close="drawerOpen = false"
        />
      </template>
    </USlideover>
  </div>
</template>
