<script setup lang="ts">
definePageMeta({ middleware: 'auth' })

const dsStore = useDataSourcesStore()
await dsStore.fetch()
</script>

<template>
  <div class="p-6 space-y-6">
    <h1 class="text-2xl font-semibold">Dashboard</h1>

    <div v-if="dsStore.loading" class="flex justify-center py-12">
      <UIcon name="lucide:loader-circle" class="animate-spin text-4xl text-primary" />
    </div>

    <div v-else-if="dsStore.list.length === 0" class="text-center py-12 space-y-3">
      <UIcon name="lucide:database" class="text-5xl text-gray-400" />
      <p class="text-gray-500">Nessuna sorgente dati. Carica il tuo primo file Excel.</p>
      <UButton to="/import" icon="lucide:upload">Importa Excel</UButton>
    </div>

    <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <UCard
        v-for="ds in dsStore.list"
        :key="ds.id"
        class="hover:ring-2 hover:ring-primary cursor-pointer transition"
        @click="navigateTo(`/source/${ds.id}`)"
      >
        <div class="flex items-center justify-between">
          <div>
            <p class="font-semibold">{{ ds.label }}</p>
            <p class="text-sm text-gray-500">{{ ds.record_count }} record</p>
          </div>
          <UIcon name="lucide:table" class="text-2xl text-primary" />
        </div>
      </UCard>
    </div>
  </div>
</template>
