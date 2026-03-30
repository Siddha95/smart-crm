interface DataSource {
  id: number
  name: string
  label: string
  columns: string[]
  stages: string[]
  source_file: string | null
  record_count: number
  created_at: string
}

interface GlobalRecord {
  id: number
  datasourceId: number
  datasourceLabel: string
  data: Record<string, any>
}

export const useDataSourcesStore = defineStore('datasources', {
  state: () => ({
    list: [] as DataSource[],
    loading: false,
    allRecords: [] as GlobalRecord[],
    allRecordsLoaded: false,
  }),

  actions: {
    async fetch() {
      const api = useApi()
      this.loading = true
      try {
        this.list = await api.get<DataSource[]>('/datasources/')
      } finally {
        this.loading = false
      }
    },

    async loadAllRecords() {
      if (this.allRecordsLoaded) return
      const api = useApi()
      const all: GlobalRecord[] = []
      let path = '/records/?page_size=200'
      while (path) {
        const raw = await api.get<{ results: any[]; next: string | null }>(path)
        all.push(...raw.results.map(r => ({
          id: r.id,
          datasourceId: r.data_source,
          datasourceLabel: this.list.find(d => d.id === r.data_source)?.label ?? '',
          data: r.data,
        })))
        path = raw.next ? '/records/' + new URL(raw.next).search : ''
      }
      this.allRecords = all
      this.allRecordsLoaded = true
    },
  },
})
