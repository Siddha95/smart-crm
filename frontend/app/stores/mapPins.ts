export interface MapPin {
  id: number
  record: number
  lat: number
  lng: number
  color: string
  created_at: string
  record_data: Record<string, any>
  datasource_label: string
  columns: string[]
}

export const useMapPinsStore = defineStore('mapPins', {
  state: () => ({
    pins: [] as MapPin[],
    loading: false,
  }),

  actions: {
    async fetch() {
      const api = useApi()
      this.loading = true
      try {
        this.pins = await api.get<MapPin[]>('/map-pins/')
      } finally {
        this.loading = false
      }
    },

    async create(payload: { record: number; lat: number; lng: number; color: string }) {
      const api = useApi()
      const pin = await api.post<MapPin>('/map-pins/', payload)
      this.pins.push(pin)
      return pin
    },

    async remove(id: number) {
      const api = useApi()
      await api.del(`/map-pins/${id}/`)
      this.pins = this.pins.filter(p => p.id !== id)
    },
  },
})
