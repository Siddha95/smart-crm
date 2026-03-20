interface DataSource {
  id: number
  name: string
  label: string
  columns: string[]
  record_count: number
  created_at: string
}

export const useDataSourcesStore = defineStore('datasources', {
  state: () => ({
    list: [] as DataSource[],
    loading: false,
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
  },
})
