<script setup lang="ts">
definePageMeta({ middleware: 'auth' })

const api = useApi()
const router = useRouter()
const toast = useToast()

const form = reactive({ name: '', label: '', file: null as File | null })
const loading = ref(false)

function onFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  form.file = input.files?.[0] ?? null
  if (form.file && !form.name) {
    // Pre-compila il nome dal filename senza estensione
    form.name = form.file.name.replace(/\.[^/.]+$/, '').toLowerCase().replace(/\s+/g, '_')
    form.label = form.file.name.replace(/\.[^/.]+$/, '')
  }
}

async function submit() {
  if (!form.file || !form.name) return

  const formData = new FormData()
  formData.append('file', form.file)
  formData.append('name', form.name)
  formData.append('label', form.label || form.name)

  loading.value = true
  try {
    await api.upload('/datasources/upload/', formData)
    toast.add({ title: 'File importato con successo.', color: 'success' })
    router.push('/dashboard')
  } catch (e: any) {
    toast.add({ title: e.message, color: 'error' })
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="p-6 max-w-lg mx-auto space-y-6">
    <div>
      <h1 class="text-2xl font-semibold">Importa Excel</h1>
      <p class="text-sm text-gray-500 mt-1">Carica un file .xlsx per creare una nuova sezione nel CRM.</p>
    </div>

    <UCard>
      <div class="space-y-4">
        <UFormField label="File Excel" required>
          <input
            type="file"
            accept=".xlsx,.xls"
            class="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-primary/10 file:text-primary hover:file:bg-primary/20 cursor-pointer"
            @change="onFileChange"
          />
        </UFormField>

        <UFormField label="Nome interno" hint="Usato come identificatore, senza spazi">
          <UInput v-model="form.name" placeholder="es. clienti" />
        </UFormField>

        <UFormField label="Etichetta" hint="Nome visualizzato nell'interfaccia">
          <UInput v-model="form.label" placeholder="es. Clienti" />
        </UFormField>

        <div class="flex gap-3 pt-2">
          <UButton :loading="loading" :disabled="!form.file || !form.name" @click="submit">
            Importa
          </UButton>
          <UButton variant="ghost" to="/dashboard">Annulla</UButton>
        </div>
      </div>
    </UCard>
  </div>
</template>
