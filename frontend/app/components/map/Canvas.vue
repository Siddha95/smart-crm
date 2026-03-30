<script setup lang="ts">
import type { MapPin } from '~/stores/mapPins'

const props = defineProps<{ pins: MapPin[] }>()
const emit = defineEmits<{
  mapClick: [lat: number, lng: number]
  pinClick: [pin: MapPin]
}>()

const mapEl = ref<HTMLDivElement>()
let L: typeof import('leaflet') | null = null
let map: import('leaflet').Map | null = null
let tileLayer: import('leaflet').TileLayer | null = null
const markers = new Map<number, import('leaflet').Marker>()

const colorMode = useColorMode()

const TILE_URL = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'
const TILE_ATTRIBUTION = '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'

function applyTileLayer() {
  if (!map || !L) return
  if (tileLayer) map.removeLayer(tileLayer)
  const isDark = colorMode.value === 'dark'
  tileLayer = L.tileLayer(TILE_URL, {
    attribution: TILE_ATTRIBUTION,
    className: isDark ? 'tiles-dark' : '',
  }).addTo(map)
}

function buildIcon(color: string) {
  return L!.divIcon({
    className: '',
    html: `<div style="
      width:26px;height:26px;border-radius:50% 50% 50% 0;
      background:${color};border:2px solid #fff;
      transform:rotate(-45deg);
      box-shadow:0 2px 6px rgba(0,0,0,.35);
    "></div>`,
    iconSize: [26, 26],
    iconAnchor: [13, 26],
  })
}

function syncMarkers() {
  if (!map || !L) return

  // Rimuovi marker non più presenti
  for (const [id, marker] of markers) {
    if (!props.pins.find(p => p.id === id)) {
      map.removeLayer(marker)
      markers.delete(id)
    }
  }

  // Aggiungi nuovi marker
  for (const pin of props.pins) {
    if (!markers.has(pin.id)) {
      const marker = L.marker([pin.lat, pin.lng], { icon: buildIcon(pin.color) }).addTo(map)
      marker.on('click', () => emit('pinClick', pin))
      markers.set(pin.id, marker)
    }
  }
}

onMounted(async () => {
  const leaflet = await import('leaflet')
  await import('leaflet/dist/leaflet.css')
  L = leaflet

  map = L.map(mapEl.value!).setView([42.5, 12.5], 6)
  applyTileLayer()

  map.on('click', (e) => emit('mapClick', e.latlng.lat, e.latlng.lng))

  syncMarkers()
})

onUnmounted(() => map?.remove())

function flyTo(lat: number, lng: number) {
  map?.flyTo([lat, lng], 13, { duration: 1 })
}

defineExpose({ flyTo })

watch(() => props.pins, syncMarkers, { deep: true })
watch(() => colorMode.value, applyTileLayer)
</script>

<template>
  <div ref="mapEl" class="w-full h-full" />
</template>

<style>
.tiles-dark {
  filter: invert(100%) hue-rotate(180deg) brightness(95%) contrast(90%);
}
</style>
