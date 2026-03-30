<script setup lang="ts">
import type { MapPin } from '~/stores/mapPins'

const props = defineProps<{ pin: MapPin | null }>()
const emit = defineEmits<{
  close: []
  delete: [pinId: number]
}>()

const open = computed({
  get: () => props.pin !== null,
  set: (v) => { if (!v) emit('close') },
})
</script>

<template>
  <UModal v-model:open="open">
    <template #title>
      <span class="text-primary text-sm font-medium">{{ pin?.datasource_label }}</span>
    </template>
    <template #body>
      <div v-if="pin" class="space-y-2">
        <div
          v-for="col in pin.columns"
          :key="col"
          class="flex gap-3 text-sm py-1 border-b border-gray-100 dark:border-gray-800 last:border-0"
        >
          <span class="font-medium text-gray-500 w-32 flex-shrink-0 truncate">{{ col }}</span>
          <span class="text-gray-900 dark:text-gray-100 break-words min-w-0">
            {{ pin.record_data[col] ?? '—' }}
          </span>
        </div>
      </div>
    </template>
    <template #footer>
      <div class="flex justify-between w-full">
        <UButton
          color="error"
          variant="soft"
          icon="lucide:map-pin-off"
          @click="pin && emit('delete', pin.id)"
        >
          Rimuovi dalla mappa
        </UButton>
        <UButton variant="ghost" @click="emit('close')">Chiudi</UButton>
      </div>
    </template>
  </UModal>
</template>
