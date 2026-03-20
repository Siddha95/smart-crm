<script setup lang="ts">
import { marked } from "marked";

const notesStore = useNotesStore();

// Carica le note quando si apre il pannello
watch(
  () => notesStore.open,
  async (val) => {
    if (val && !notesStore.loaded) {
      await notesStore.fetch();
    }
  },
);

const preview = ref(false);

// Debounce autosave: salva 800ms dopo l'ultima modifica
let saveTimer: ReturnType<typeof setTimeout> | null = null;

function onTitleInput(val: string) {
  if (!notesStore.activeId) return;
  const note = notesStore.active;
  if (!note) return;
  note.title = val;
  scheduleSave({ title: val });
}

function onContentInput(val: string) {
  if (!notesStore.activeId) return;
  const note = notesStore.active;
  if (!note) return;
  note.content = val;
  scheduleSave({ content: val });
}

function scheduleSave(patch: { title?: string; content?: string }) {
  if (saveTimer) clearTimeout(saveTimer);
  saveTimer = setTimeout(() => {
    if (notesStore.activeId) notesStore.save(notesStore.activeId, patch);
  }, 800);
}

const renderedContent = computed(() => {
  const content = notesStore.active?.content ?? "";
  return marked.parse(content) as string;
});

async function addNote() {
  await notesStore.create();
  preview.value = false;
}

async function deleteNote() {
  if (notesStore.activeId) await notesStore.remove(notesStore.activeId);
}
</script>

<template>
  <USlideover
    v-model:open="notesStore.open"
    title="Note"
    side="right"
    class="max-w-2xl"
  >
    <template #body>
      <div class="flex h-full gap-0">
        <!-- Lista note -->
        <div
          class="w-52 flex-shrink-0 border-r border-gray-200 dark:border-gray-700 flex flex-col"
        >
          <div class="p-3 border-b border-gray-200 dark:border-gray-700">
            <UButton
              icon="lucide:plus"
              size="xs"
              variant="soft"
              block
              @click="addNote"
            >
              Nuova nota
            </UButton>
          </div>

          <div class="flex-1 overflow-y-auto">
            <button
              v-for="note in notesStore.list"
              :key="note.id"
              class="w-full text-left px-3 py-2.5 border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
              :class="
                notesStore.activeId === note.id
                  ? 'bg-primary/5 border-l-2 border-l-primary'
                  : ''
              "
              @click="notesStore.activeId = note.id"
            >
              <p class="text-sm font-medium truncate">
                {{ note.title || "Senza titolo" }}
              </p>
              <p class="text-xs text-gray-400 mt-0.5">
                {{ new Date(note.updated_at).toLocaleDateString("it-IT") }}
              </p>
            </button>

            <div
              v-if="!notesStore.list.length"
              class="p-4 text-center text-sm text-gray-400"
            >
              Nessuna nota.<br />Creane una!
            </div>
          </div>
        </div>

        <!-- Editor -->
        <div class="flex-1 flex flex-col min-w-0" v-if="notesStore.active">
          <!-- Toolbar -->
          <div
            class="flex items-center justify-between px-4 py-2 border-b border-gray-200 dark:border-gray-700 gap-2"
          >
            <UInput
              :model-value="notesStore.active.title"
              placeholder="Titolo nota"
              variant="ghost"
              class="flex-1 font-medium"
              @update:model-value="onTitleInput"
            />
            <div class="flex items-center gap-1">
              <UTooltip :text="preview ? 'Modifica' : 'Anteprima markdown'">
                <UButton
                  :icon="preview ? 'lucide:pencil' : 'lucide:eye'"
                  variant="ghost"
                  size="xs"
                  color="neutral"
                  @click="preview = !preview"
                />
              </UTooltip>
              <UTooltip text="Elimina nota">
                <UButton
                  icon="lucide:trash-2"
                  variant="ghost"
                  size="xs"
                  color="error"
                  @click="deleteNote"
                />
              </UTooltip>
              <UBadge
                v-if="notesStore.saving"
                label="Salvataggio..."
                variant="soft"
                size="xs"
              />
            </div>
          </div>

          <!-- Contenuto: editor o preview -->
          <div class="flex-1 overflow-y-auto p-4">
            <textarea
              v-if="!preview"
              :value="notesStore.active.content"
              placeholder="Scrivi qui... supporta markdown: **grassetto**, # titoli, - liste"
              class="w-full h-full min-h-[400px] resize-none bg-transparent text-sm font-mono outline-none text-gray-800 dark:text-gray-200 placeholder-gray-400"
              @input="
                onContentInput(($event.target as HTMLTextAreaElement).value)
              "
            />
            <div
              v-else
              class="prose prose-sm dark:prose-invert max-w-none"
              v-html="renderedContent"
            />
          </div>
        </div>

        <!-- Placeholder nessuna nota selezionata -->
        <div
          v-else
          class="flex-1 flex items-center justify-center text-gray-400 text-sm"
        >
          Seleziona o crea una nota
        </div>
      </div>
    </template>
  </USlideover>
</template>
