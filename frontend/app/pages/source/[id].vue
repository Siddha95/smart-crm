<script setup lang="ts">
import type { ColumnDef, SortingState } from '@tanstack/vue-table'

definePageMeta({ middleware: 'auth' })

const route = useRoute()
const api = useApi()
const dsStore = useDataSourcesStore()

const datasourceId = Number(route.params.id)
const datasource = computed(() => dsStore.list.find(d => d.id === datasourceId))

const records = ref<Record<string, any>[]>([])
const loading = ref(true)
const search = ref('')
const sorting = ref<SortingState>([])
const selectedRecord = ref<any>(null)
const drawerOpen = computed({
  get: () => !!selectedRecord.value,
  set: (v) => { if (!v) selectedRecord.value = null }
})

await dsStore.fetch()

async function fetchRecords() {
  loading.value = true
  try {
    const data = await api.get<any[]>(`/records/?data_source=${datasourceId}`)
    records.value = data
  } finally {
    loading.value = false
  }
}

await fetchRecords()

const filteredRecords = computed(() => {
  if (!search.value) return records.value
  const q = search.value.toLowerCase()
  return records.value.filter(r =>
    Object.values(r.data).some(v => String(v).toLowerCase().includes(q))
  )
})

const columns = computed<ColumnDef<any>[]>(() =>
  (datasource.value?.columns ?? []).map(col => ({
    accessorKey: col,
    header: col,
    enableSorting: true,
    enableColumnFilter: true,
  }))
)

const rows = computed(() =>
  filteredRecords.value.map(r => ({ _id: r.id, ...r.data }))
)
</script>

<template>
  <div class="p-6 space-y-4">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-semibold">{{ datasource?.label }}</h1>
        <p class="text-sm text-gray-500">{{ records.length }} record</p>
      </div>
      <UInput v-model="search" icon="lucide:search" placeholder="Cerca in tutti i campi..." class="w-72" />
    </div>

    <UTable
      :data="rows"
      :columns="columns"
      :loading="loading"
      v-model:sorting="sorting"
      :ui="{ td: 'whitespace-normal align-top', tdText: 'whitespace-normal overflow-visible' }"
      @select="row => selectedRecord = records.find(r => r.id === row._id)"
    />

    <USlideover v-model:open="drawerOpen">
      <template #title>Dettaglio record</template>
      <RecordDetail
        v-if="selectedRecord"
        :record="selectedRecord"
        :columns="datasource?.columns ?? []"
        @updated="fetchRecords"
        @close="selectedRecord = null"
      />
    </USlideover>
  </div>
</template>
