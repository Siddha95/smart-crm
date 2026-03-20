<script setup lang="ts">
definePageMeta({ middleware: 'auth' })

const api = useApi()
const router = useRouter()
const toast = useToast()

interface SheetPreview {
  name: string
  columns: string[]
  rows: Record<string, any>[]
}

const form = reactive({ name: '', file: null as File | null })
const loading = ref(false)
const preview = ref<SheetPreview[] | null>(null)

function onFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  form.file = input.files?.[0] ?? null
  preview.value = null
  if (form.file && !form.name) {
    form.name = form.file.name.replace(/\.[^/.]+$/, '').toLowerCase().replace(/\s+/g, '_')
  }
}

async function loadPreview() {
  if (!form.file) return
  const formData = new FormData()
  formData.append('file', form.file)
  loading.value = true
  try {
    const result = await api.upload<{ sheets: SheetPreview[] }>('/datasources/preview/', formData)
    preview.value = result.sheets
  } catch (e: any) {
    toast.add({ title: e.message, color: 'error' })
  } finally {
    loading.value = false
  }
}

async function submit() {
  if (!form.file || !form.name) return
  const formData = new FormData()
  formData.append('file', form.file)
  formData.append('name', form.name)
  loading.value = true
  try {
    const result = await api.upload<{ sheets: any[] }>('/datasources/upload/', formData)
    const count = result?.sheets?.length ?? 1
    toast.add({ title: `File importato: ${count} ${count === 1 ? 'foglio' : 'fogli'}.`, color: 'success' })
    router.push('/dashboard')
  } catch (e: any) {
    toast.add({ title: e.message, color: 'error' })
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="p-6 max-w-3xl mx-auto space-y-6">
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

        <UFormField label="Nome interno" hint="Identificatore del file — i fogli useranno questo come prefisso">
          <UInput v-model="form.name" placeholder="es. clienti" />
        </UFormField>

        <div class="flex gap-3 pt-2">
          <UButton
            v-if="!preview"
            variant="outline"
            :loading="loading"
            :disabled="!form.file || !form.name"
            icon="lucide:eye"
            @click="loadPreview"
          >
            Anteprima
          </UButton>

          <UButton
            :loading="loading"
            :disabled="!form.file || !form.name"
            icon="lucide:upload"
            @click="submit"
          >
            {{ preview ? 'Conferma importazione' : 'Importa' }}
          </UButton>

          <UButton variant="ghost" to="/dashboard">Annulla</UButton>
        </div>
      </div>
    </UCard>

    <!-- Anteprima fogli -->
    <template v-if="preview">
      <UCard v-for="sheet in preview" :key="sheet.name">
        <template #header>
          <div class="flex items-center gap-2">
            <UIcon name="lucide:table" class="text-primary" />
            <span class="font-medium">{{ sheet.name }}</span>
            <span class="text-sm text-gray-400">({{ sheet.columns.length }} colonne)</span>
          </div>
        </template>

        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b">
                <th
                  v-for="col in sheet.columns"
                  :key="col"
                  class="text-left py-2 px-3 font-medium text-gray-500 whitespace-nowrap"
                >
                  {{ col }}
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, i) in sheet.rows" :key="i" class="border-b last:border-0">
                <td
                  v-for="col in sheet.columns"
                  :key="col"
                  class="py-2 px-3 text-gray-700 dark:text-gray-300 whitespace-nowrap max-w-48 truncate"
                >
                  {{ row[col] ?? '—' }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <template #footer>
          <p class="text-xs text-gray-400">Mostra le prime {{ sheet.rows.length }} righe</p>
        </template>
      </UCard>
    </template>
  </div>
</template>
