<script setup lang="ts">
const emit = defineEmits<{
  locate: [lat: number, lng: number, label: string]
}>()

interface NominatimResult {
  lat: string
  lon: string
  display_name: string
}

const query = ref('')
const results = ref<NominatimResult[]>([])
const loading = ref(false)
const showResults = ref(false)

let debounceTimer: ReturnType<typeof setTimeout> | null = null

async function search() {
  const q = query.value.trim()
  if (q.length < 2) { results.value = []; return }

  loading.value = true
  try {
    const res = await fetch(
      `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(q)}&format=json&limit=5&countrycodes=it`,
      { headers: { 'Accept-Language': 'it' } }
    )
    results.value = await res.json()
    showResults.value = true
  } finally {
    loading.value = false
  }
}

function onInput() {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(search, 400)
}

function select(r: NominatimResult) {
  emit('locate', parseFloat(r.lat), parseFloat(r.lon), r.display_name)
  query.value = r.display_name.split(',')[0]
  showResults.value = false
  results.value = []
}

function onBlur() {
  setTimeout(() => { showResults.value = false }, 150)
}
</script>

<template>
  <div class="relative w-72">
    <UInput
      v-model="query"
      icon="lucide:search"
      :loading="loading"
      placeholder="Cerca città, indirizzo..."
      @input="onInput"
      @focus="showResults = results.length > 0"
      @blur="onBlur"
    />
    <div
      v-if="showResults && results.length"
      class="absolute z-[1000] top-full mt-1 w-full bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg overflow-hidden"
    >
      <button
        v-for="r in results"
        :key="r.display_name"
        class="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 dark:hover:bg-gray-800 border-b border-gray-100 dark:border-gray-800 last:border-0 transition-colors"
        @mousedown="select(r)"
      >
        <p class="font-medium truncate">{{ r.display_name.split(',')[0] }}</p>
        <p class="text-xs text-gray-400 truncate">{{ r.display_name.split(',').slice(1, 3).join(',') }}</p>
      </button>
    </div>
  </div>
</template>
