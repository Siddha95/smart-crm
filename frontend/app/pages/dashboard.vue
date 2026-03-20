<script setup lang="ts">
definePageMeta({ middleware: 'auth' })

const api = useApi()
const toast = useToast()
const router = useRouter()
const dsStore = useDataSourcesStore()
await dsStore.fetch()

// ─── Raggruppa per source_file ───────────────────────────────────────────────
const groups = computed(() => {
  const map = new Map<string, { key: string; label: string; firstId: number; totalRecords: number }>()
  for (const ds of dsStore.list) {
    const key = ds.source_file ?? String(ds.id)
    if (!map.has(key)) {
      map.set(key, { key, label: ds.source_file ?? ds.label, firstId: ds.id, totalRecords: 0 })
    }
    map.get(key)!.totalRecords += ds.record_count
  }
  return [...map.values()]
})

// ─── Ricerca globale ─────────────────────────────────────────────────────────
const globalSearch = ref('')
const searchFocused = ref(false)

async function onSearchFocus() {
  searchFocused.value = true
  await dsStore.loadAllRecords()
}

const searchResults = computed(() => {
  const q = globalSearch.value.trim().toLowerCase()
  if (!q || q.length < 2) return []
  return dsStore.allRecords
    .filter(r => Object.values(r.data).some(v => String(v).toLowerCase().includes(q)))
    .slice(0, 20)
})

function goToRecord(record: { datasourceId: number }) {
  globalSearch.value = ''
  searchFocused.value = false
  router.push(`/source/${record.datasourceId}`)
}

// ─── Export ─────────────────────────────────────────────────────────────────
async function exportGroup(group: { key: string; label: string }, fmt: 'xlsx' | 'pdf') {
  try {
    await api.download(
      `/datasources/export_group/?source_file=${encodeURIComponent(group.key)}&fmt=${fmt}`,
      `${group.label}.${fmt}`,
    )
  } catch (e: any) {
    toast.add({ title: e.message, color: 'error' })
  }
}

// ─── Rinomina ───────────────────────────────────────────────────────────────
const renameTarget = ref<{ key: string; label: string } | null>(null)
const renameValue = ref('')
const renaming = ref(false)

function openRename(group: { key: string; label: string }) {
  renameTarget.value = group
  renameValue.value = group.label
}

const renameModalOpen = computed({
  get: () => !!renameTarget.value,
  set: (v) => { if (!v) renameTarget.value = null },
})

async function confirmRename() {
  if (!renameTarget.value || !renameValue.value.trim()) return
  renaming.value = true
  try {
    await api.patch('/datasources/rename_group/', {
      source_file: renameTarget.value.key,
      new_name: renameValue.value.trim(),
    })
    toast.add({ title: 'Rinominato con successo.', color: 'success' })
    renameTarget.value = null
    dsStore.allRecordsLoaded = false
    await dsStore.fetch()
  } catch (e: any) {
    toast.add({ title: e.message, color: 'error' })
  } finally {
    renaming.value = false
  }
}

// ─── Elimina ────────────────────────────────────────────────────────────────
const deleteTarget = ref<{ key: string; label: string } | null>(null)
const deleting = ref(false)

function openDelete(group: { key: string; label: string }) {
  deleteTarget.value = group
}

const deleteModalOpen = computed({
  get: () => !!deleteTarget.value,
  set: (v) => { if (!v) deleteTarget.value = null },
})

async function confirmDelete() {
  if (!deleteTarget.value) return
  deleting.value = true
  try {
    await api.del(`/datasources/delete_group/?source_file=${encodeURIComponent(deleteTarget.value.key)}`)
    toast.add({ title: 'Eliminato con successo.', color: 'success' })
    deleteTarget.value = null
    dsStore.allRecordsLoaded = false
    await dsStore.fetch()
    if (dsStore.list.length === 0) router.push('/import')
  } catch (e: any) {
    toast.add({ title: e.message, color: 'error' })
  } finally {
    deleting.value = false
  }
}
</script>

<template>
  <div class="p-6 space-y-6">
    <div class="flex items-center justify-between gap-4 flex-wrap">
      <h1 class="text-2xl font-semibold">Dashboard</h1>

      <!-- Ricerca globale -->
      <div class="relative w-72">
        <UInput
          v-model="globalSearch"
          icon="lucide:search"
          placeholder="Cerca in tutti i datasource..."
          class="w-full"
          @focus="onSearchFocus"
          @blur="setTimeout(() => { searchFocused = false }, 150)"
        />
        <!-- Risultati -->
        <div
          v-if="searchFocused && globalSearch.length >= 2"
          class="absolute z-50 top-full mt-1 w-full bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg max-h-80 overflow-y-auto"
        >
          <div v-if="dsStore.allRecords.length === 0 && !dsStore.allRecordsLoaded" class="p-3 text-sm text-gray-400 text-center">
            <UIcon name="lucide:loader-circle" class="animate-spin mr-1" /> Caricamento...
          </div>
          <div v-else-if="searchResults.length === 0" class="p-3 text-sm text-gray-400 text-center">
            Nessun risultato.
          </div>
          <button
            v-for="result in searchResults"
            :key="result.id"
            class="w-full text-left px-3 py-2 hover:bg-gray-50 dark:hover:bg-gray-800 border-b border-gray-100 dark:border-gray-800 last:border-0 cursor-pointer"
            @mousedown="goToRecord(result)"
          >
            <p class="text-xs text-primary font-medium">{{ result.datasourceLabel }}</p>
            <p class="text-sm truncate text-gray-700 dark:text-gray-300">
              {{ Object.values(result.data).slice(0, 3).join(' · ') }}
            </p>
          </button>
        </div>
      </div>
    </div>

    <div v-if="dsStore.loading" class="flex justify-center py-12">
      <UIcon name="lucide:loader-circle" class="animate-spin text-4xl text-primary" />
    </div>

    <div v-else-if="groups.length === 0" class="text-center py-12 space-y-3">
      <UIcon name="lucide:database" class="text-5xl text-gray-400" />
      <p class="text-gray-500">Nessuna sorgente dati. Carica il tuo primo file Excel.</p>
      <UButton to="/import" icon="lucide:upload">Importa Excel</UButton>
    </div>

    <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <UCard
        v-for="group in groups"
        :key="group.key"
        class="hover:ring-2 hover:ring-primary transition cursor-pointer"
        @click="navigateTo(`/source/${group.firstId}`)"
      >
        <div class="flex items-center justify-between">
          <div class="min-w-0">
            <p class="font-semibold truncate">{{ group.label }}</p>
            <p class="text-sm text-gray-500">{{ group.totalRecords }} record</p>
          </div>
          <div @click.stop>
            <UDropdownMenu
              :items="[
                [
                  { label: 'Rinomina', icon: 'lucide:pencil', onSelect: () => openRename(group) },
                  { label: 'Export Excel (.xlsx)', icon: 'lucide:table', onSelect: () => exportGroup(group, 'xlsx') },
                  { label: 'Export PDF', icon: 'lucide:file-text', onSelect: () => exportGroup(group, 'pdf') },
                ],
                [{ label: 'Elimina', icon: 'lucide:trash-2', color: 'error', onSelect: () => openDelete(group) }],
              ]"
            >
              <UButton size="xs" variant="ghost" icon="lucide:ellipsis-vertical" />
            </UDropdownMenu>
          </div>
        </div>
      </UCard>
    </div>

    <!-- Modal rinomina -->
    <UModal v-model:open="renameModalOpen">
      <template #title>Rinomina</template>
      <template #body>
        <UInput v-model="renameValue" placeholder="Nuovo nome..." @keydown.enter="confirmRename" />
      </template>
      <template #footer>
        <div class="flex gap-2 justify-end">
          <UButton variant="ghost" @click="renameTarget = null">Annulla</UButton>
          <UButton :loading="renaming" :disabled="!renameValue.trim()" @click="confirmRename">
            Rinomina
          </UButton>
        </div>
      </template>
    </UModal>

    <!-- Modal elimina -->
    <UModal v-model:open="deleteModalOpen">
      <template #title>Elimina "{{ deleteTarget?.label }}"</template>
      <template #body>
        <p class="text-sm">
          Verranno eliminati tutti i fogli e i record associati. L'operazione non è reversibile.
        </p>
      </template>
      <template #footer>
        <div class="flex gap-2 justify-end">
          <UButton variant="ghost" @click="deleteTarget = null">Annulla</UButton>
          <UButton color="error" :loading="deleting" @click="confirmDelete">Elimina</UButton>
        </div>
      </template>
    </UModal>
  </div>
</template>
