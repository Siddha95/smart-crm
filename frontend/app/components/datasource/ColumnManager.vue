<script setup lang="ts">
const props = defineProps<{
  datasourceId: number
  columns: string[]
}>()

const emit = defineEmits<{ updated: [] }>()

const api = useApi()
const toast = useToast()

// ─── Stato locale colonne (copia modificabile) ─────────────────────────────
const cols = ref([...props.columns])
watch(() => props.columns, (v) => { cols.value = [...v] })

// ─── Rinomina inline ───────────────────────────────────────────────────────
const editingIndex = ref<number | null>(null)
const editingValue = ref('')

function startEdit(i: number) {
  editingIndex.value = i
  editingValue.value = cols.value[i]
}

async function commitRename(i: number) {
  const oldName = cols.value[i]
  const newName = editingValue.value.trim()
  editingIndex.value = null
  if (!newName || newName === oldName) return
  try {
    await api.post(`/datasources/${props.datasourceId}/columns/`, {
      operation: 'rename', old_name: oldName, new_name: newName,
    })
    toast.add({ title: `"${oldName}" rinominata in "${newName}".`, color: 'success' })
    emit('updated')
  } catch (e: any) {
    toast.add({ title: e.message, color: 'error' })
  }
}

// ─── Elimina colonna ───────────────────────────────────────────────────────
const confirmDeleteCol = ref<string | null>(null)
const deleting = ref(false)

async function deleteColumn() {
  if (!confirmDeleteCol.value) return
  deleting.value = true
  try {
    await api.post(`/datasources/${props.datasourceId}/columns/`, {
      operation: 'delete', name: confirmDeleteCol.value,
    })
    toast.add({ title: `Colonna "${confirmDeleteCol.value}" eliminata.`, color: 'success' })
    confirmDeleteCol.value = null
    emit('updated')
  } catch (e: any) {
    toast.add({ title: e.message, color: 'error' })
  } finally {
    deleting.value = false
  }
}

// ─── Riordina colonne via drag & drop ──────────────────────────────────────
const dragIndex = ref<number | null>(null)

function onDragStart(i: number) {
  dragIndex.value = i
}

function onDragOver(e: DragEvent, i: number) {
  e.preventDefault()
  if (dragIndex.value === null || dragIndex.value === i) return
  const arr = [...cols.value]
  const [moved] = arr.splice(dragIndex.value, 1)
  arr.splice(i, 0, moved)
  cols.value = arr
  dragIndex.value = i
}

async function onDragEnd() {
  dragIndex.value = null
  try {
    await api.post(`/datasources/${props.datasourceId}/columns/`, {
      operation: 'reorder', columns: cols.value,
    })
    emit('updated')
  } catch (e: any) {
    toast.add({ title: e.message, color: 'error' })
  }
}

// ─── Aggiungi colonna ──────────────────────────────────────────────────────
const newColName = ref('')
const adding = ref(false)

async function addColumn() {
  const name = newColName.value.trim()
  if (!name) return
  adding.value = true
  try {
    await api.post(`/datasources/${props.datasourceId}/columns/`, {
      operation: 'add', name,
    })
    toast.add({ title: `Colonna "${name}" aggiunta.`, color: 'success' })
    newColName.value = ''
    emit('updated')
  } catch (e: any) {
    toast.add({ title: e.message, color: 'error' })
  } finally {
    adding.value = false
  }
}
</script>

<template>
  <div class="space-y-3">
    <!-- Lista colonne esistenti -->
    <div
      v-for="(col, i) in cols"
      :key="col"
      draggable="true"
      class="flex items-center gap-2 group rounded px-1 transition-opacity"
      :class="dragIndex === i ? 'opacity-40' : ''"
      @dragstart="onDragStart(i)"
      @dragover="onDragOver($event, i)"
      @dragend="onDragEnd"
    >
      <UIcon name="lucide:grip-vertical" class="text-gray-400 cursor-grab shrink-0" />

      <!-- Rinomina inline -->
      <template v-if="editingIndex === i">
        <UInput
          v-model="editingValue"
          class="flex-1"
          size="sm"
          autofocus
          @keydown.enter="commitRename(i)"
          @keydown.escape="editingIndex = null"
        />
        <UButton size="xs" icon="lucide:check" @click="commitRename(i)" />
        <UButton size="xs" variant="ghost" icon="lucide:x" @click="editingIndex = null" />
      </template>

      <template v-else>
        <span class="flex-1 text-sm">{{ col }}</span>
        <div class="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <UButton size="xs" variant="ghost" icon="lucide:pencil" @click="startEdit(i)" />
          <UButton
            size="xs"
            variant="ghost"
            color="error"
            icon="lucide:trash-2"
            @click="confirmDeleteCol = col"
          />
        </div>
      </template>
    </div>

    <!-- Conferma eliminazione colonna -->
    <div v-if="confirmDeleteCol" class="flex items-center gap-2 p-2 rounded bg-red-50 dark:bg-red-950 text-sm">
      <span class="flex-1 text-red-600 dark:text-red-400">
        Eliminare "{{ confirmDeleteCol }}" da tutti i record?
      </span>
      <UButton size="xs" color="error" :loading="deleting" @click="deleteColumn">Sì</UButton>
      <UButton size="xs" variant="ghost" @click="confirmDeleteCol = null">No</UButton>
    </div>

    <!-- Aggiungi nuova colonna -->
    <div class="flex gap-2 pt-2 border-t">
      <UInput
        v-model="newColName"
        placeholder="Nome nuova colonna..."
        size="sm"
        class="flex-1"
        @keydown.enter="addColumn"
      />
      <UButton size="xs" icon="lucide:plus" :loading="adding" :disabled="!newColName.trim()" @click="addColumn">
        Aggiungi
      </UButton>
    </div>
  </div>
</template>
