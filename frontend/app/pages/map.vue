<script setup lang="ts">
import type { MapPin } from '~/stores/mapPins'

definePageMeta({ middleware: 'auth' })

const pinsStore = useMapPinsStore()
const toast = useToast()

await pinsStore.fetch()

const canvas = ref<{ flyTo: (lat: number, lng: number) => void } | null>(null)
const pendingCoords = ref<{ lat: number; lng: number } | null>(null)
const selectedPin = ref<MapPin | null>(null)

// Colori usati dai pin esistenti
const activeColors = computed(() => [...new Set(pinsStore.pins.map(p => p.color))])

// Colori attualmente visibili (tutti attivi di default)
const visibleColors = ref<Set<string>>(new Set())
watch(activeColors, (colors) => {
  colors.forEach(c => visibleColors.value.add(c))
}, { immediate: true })

function toggleColor(color: string) {
  if (visibleColors.value.has(color)) visibleColors.value.delete(color)
  else visibleColors.value.add(color)
  visibleColors.value = new Set(visibleColors.value)
}

const filteredPins = computed(() =>
  pinsStore.pins.filter(p => visibleColors.value.has(p.color))
)

const pickerOpen = computed({
  get: () => pendingCoords.value !== null,
  set: (v) => { if (!v) pendingCoords.value = null },
})

function onMapClick(lat: number, lng: number) {
  pendingCoords.value = { lat, lng }
}

async function onRecordConfirmed(recordId: number, color: string) {
  if (!pendingCoords.value) return
  try {
    await pinsStore.create({ record: recordId, color, ...pendingCoords.value })
    toast.add({ title: 'Pin aggiunto.', color: 'success' })
  } catch (e: any) {
    toast.add({ title: e.message, color: 'error' })
  } finally {
    pendingCoords.value = null
  }
}

async function onDeletePin(pinId: number) {
  try {
    await pinsStore.remove(pinId)
    selectedPin.value = null
    toast.add({ title: 'Pin rimosso.', color: 'success' })
  } catch (e: any) {
    toast.add({ title: e.message, color: 'error' })
  }
}
</script>

<template>
  <div class="h-[calc(100vh-4rem)] w-full relative">
    <MapCanvas
      ref="canvas"
      :pins="filteredPins"
      @map-click="onMapClick"
      @pin-click="selectedPin = $event"
    />

    <!-- Controlli in alto a destra -->
    <div class="absolute top-3 right-3 z-[1000] flex items-center gap-2">
      <!-- Filtro colori (visibile solo se ci sono pin) -->
      <div
        v-if="activeColors.length"
        class="flex items-center gap-1.5 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg px-3 py-2 shadow"
      >
        <span class="text-xs text-gray-400 mr-1">Filtro:</span>
        <button
          v-for="color in activeColors"
          :key="color"
          class="w-5 h-5 rounded-full border-2 transition-all"
          :style="{
            backgroundColor: color,
            borderColor: visibleColors.has(color) ? 'white' : 'transparent',
            opacity: visibleColors.has(color) ? 1 : 0.3,
          }"
          @click="toggleColor(color)"
        />
      </div>

      <MapSearchBar @locate="(lat, lng) => canvas?.flyTo(lat, lng)" />
    </div>

    <MapRecordPicker
      v-model:open="pickerOpen"
      :lat="pendingCoords?.lat ?? 0"
      :lng="pendingCoords?.lng ?? 0"
      @confirm="(id, color) => onRecordConfirmed(id, color)"
    />

    <MapPinDetail
      :pin="selectedPin"
      @close="selectedPin = null"
      @delete="onDeletePin"
    />
  </div>
</template>
