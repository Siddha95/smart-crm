<script setup lang="ts">
definePageMeta({ middleware: 'auth' })

const api = useApi()
const toast = useToast()

// ─── Profilo ────────────────────────────────────────────────────────────────
interface Profile { id: number; username: string; email: string; has_api_key: boolean }

const profiles = await api.get<Profile[]>('/profile/')
const profile = profiles[0] ?? null

// ─── API Key ────────────────────────────────────────────────────────────────
// Il valore della chiave non viene mai restituito dal server (write_only).
// L'utente inserisce la nuova chiave solo quando vuole aggiornarla.
const apiKey = ref('')
const showKey = ref(false)
const saving = ref(false)

async function saveKey(keyValue: string) {
  if (!profile) return
  saving.value = true
  try {
    await api.patch(`/profile/${profile.id}/api-key/`, { personal_api_key: keyValue })
    toast.add({ title: keyValue ? 'API key salvata.' : 'API key rimossa.', color: 'success' })
    if (profile) profile.has_api_key = !!keyValue
    apiKey.value = ''
    showKey.value = false
  } catch (e: any) {
    toast.add({ title: e.message, color: 'error' })
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="p-6 max-w-xl mx-auto space-y-6">
    <h1 class="text-2xl font-semibold">Impostazioni</h1>

    <!-- Profilo (sola lettura) -->
    <UCard>
      <template #header>
        <div class="flex items-center gap-2">
          <UIcon name="lucide:user" class="text-primary" />
          <span class="font-medium">Profilo</span>
        </div>
      </template>
      <dl class="space-y-2 text-sm">
        <div class="flex gap-2">
          <dt class="text-gray-500 w-24 shrink-0">Username</dt>
          <dd class="font-medium">{{ profile?.username ?? '—' }}</dd>
        </div>
        <div class="flex gap-2">
          <dt class="text-gray-500 w-24 shrink-0">Email</dt>
          <dd class="font-medium">{{ profile?.email ?? '—' }}</dd>
        </div>
      </dl>
    </UCard>

    <!-- API Key -->
    <UCard>
      <template #header>
        <div class="flex items-center gap-2">
          <UIcon name="lucide:key" class="text-primary" />
          <span class="font-medium">API Key AI</span>
        </div>
      </template>

      <div class="space-y-4">
        <p class="text-sm text-gray-500">
          La chiave viene salvata sul server e non è mai visibile dopo il salvataggio.
          Usala per abilitare l'assistente AI.
        </p>

        <div class="flex items-center gap-2 text-sm">
          <UIcon
            :name="profile?.has_api_key ? 'lucide:check-circle' : 'lucide:x-circle'"
            :class="profile?.has_api_key ? 'text-green-500' : 'text-gray-400'"
          />
          <span :class="profile?.has_api_key ? 'text-green-600 dark:text-green-400' : 'text-gray-400'">
            {{ profile?.has_api_key ? 'API key configurata' : 'Nessuna API key configurata' }}
          </span>
        </div>

        <UFormField label="Nuova API Key">
          <div class="flex gap-2">
            <UInput
              v-model="apiKey"
              :type="showKey ? 'text' : 'password'"
              placeholder="sk-ant-..."
              class="flex-1 font-mono"
              autocomplete="new-password"
              spellcheck="false"
            />
            <UButton
              :icon="showKey ? 'lucide:eye-off' : 'lucide:eye'"
              variant="outline"
              color="neutral"
              @click="showKey = !showKey"
            />
          </div>
        </UFormField>

        <div class="flex gap-2">
          <UButton
            icon="lucide:save"
            :loading="saving"
            :disabled="!apiKey.trim()"
            @click="saveKey(apiKey.trim())"
          >
            Salva
          </UButton>
          <UButton
            variant="outline"
            color="error"
            icon="lucide:trash-2"
            :loading="saving"
            @click="saveKey('')"
          >
            Rimuovi chiave
          </UButton>
        </div>
      </div>
    </UCard>
  </div>
</template>
