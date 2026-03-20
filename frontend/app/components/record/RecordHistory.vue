<script setup lang="ts">
const props = defineProps<{ recordId: number }>()

const api = useApi()

interface HistoryEntry {
  id: number
  field_changed: string
  old_value: string
  new_value: string
  changed_by: string
  changed_at: string
}

const history = ref<HistoryEntry[]>([])
await api.get<HistoryEntry[]>(`/records/${props.recordId}/history/`).then(d => history.value = d)
</script>

<template>
  <div class="space-y-2">
    <div v-if="history.length === 0" class="text-sm text-gray-400 py-4 text-center">
      Nessuna modifica registrata.
    </div>

    <div
      v-for="entry in history"
      :key="entry.id"
      class="text-sm border-l-2 border-primary pl-3 py-1 space-y-0.5"
    >
      <p>
        <span class="font-medium">{{ entry.field_changed }}</span>:
        <span class="text-gray-400 line-through">{{ entry.old_value }}</span>
        → <span>{{ entry.new_value }}</span>
      </p>
      <p class="text-xs text-gray-400">
        {{ entry.changed_by }} · {{ new Date(entry.changed_at).toLocaleString('it-IT') }}
      </p>
    </div>
  </div>
</template>
