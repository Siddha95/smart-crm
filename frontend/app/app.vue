<script setup lang="ts">
useHead({
  meta: [{ name: 'viewport', content: 'width=device-width, initial-scale=1' }],
  link: [{ rel: 'icon', href: '/favicon.ico' }],
  htmlAttrs: { lang: 'it' }
})

useSeoMeta({ title: 'Smart CRM' })

const authStore = useAuthStore()
const chatStore = useChatStore()
const notesStore = useNotesStore()
const router = useRouter()

function logout() {
  authStore.logout()
  router.push('/login')
}
</script>

<template>
  <UApp>
    <UHeader v-if="authStore.isAuthenticated">
      <template #left>
        <NuxtLink to="/dashboard">
          <AppLogo />
        </NuxtLink>
      </template>

      <template #right>
        <UButton icon="lucide:map" variant="ghost" to="/map">Mappa</UButton>
        <UButton icon="lucide:upload" variant="ghost" to="/import">Importa</UButton>
        <UButton icon="lucide:notebook-pen" variant="ghost" @click="notesStore.open = true">
          Note
        </UButton>
        <UButton icon="lucide:bot" variant="ghost" @click="chatStore.open = true">
          AI
        </UButton>
        <UColorModeButton />
        <UButton icon="lucide:settings" variant="ghost" color="neutral" to="/settings" />
        <UButton icon="lucide:log-out" variant="ghost" color="neutral" @click="logout" />
      </template>
    </UHeader>

    <UMain>
      <NuxtPage />
    </UMain>

    <!-- Chat AI sempre accessibile -->
    <AiChatSidebar />

    <!-- Taccuino note -->
    <TacquinoSlideover />
  </UApp>
</template>
