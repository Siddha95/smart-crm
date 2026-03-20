interface Note {
  id: number
  title: string
  content: string
  created_at: string
  updated_at: string
}

export const useNotesStore = defineStore('notes', {
  state: () => ({
    open: false,
    list: [] as Note[],
    loaded: false,
    activeId: null as number | null,
    saving: false,
  }),

  getters: {
    active: (state) => state.list.find(n => n.id === state.activeId) ?? null,
  },

  actions: {
    async fetch() {
      const api = useApi()
      this.list = await api.get<Note[]>('/notes/')
      this.loaded = true
      if (this.list.length && !this.activeId) {
        this.activeId = this.list[0]?.id ?? null
      }
    },

    async create() {
      const api = useApi()
      const note = await api.post<Note>('/notes/', { title: 'Nuova nota', content: '' })
      this.list.unshift(note)
      this.activeId = note.id
    },

    async save(id: number, patch: Partial<Pick<Note, 'title' | 'content'>>) {
      const api = useApi()
      this.saving = true
      try {
        const updated = await api.patch<Note>(`/notes/${id}/`, patch)
        const idx = this.list.findIndex(n => n.id === id)
        if (idx !== -1) this.list[idx] = updated
      } finally {
        this.saving = false
      }
    },

    async remove(id: number) {
      const api = useApi()
      await api.del(`/notes/${id}/`)
      this.list = this.list.filter(n => n.id !== id)
      if (this.activeId === id) {
        this.activeId = this.list[0]?.id ?? null
      }
    },
  },
})
