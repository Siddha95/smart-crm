<script setup lang="ts">
useHead({
  meta: [{ name: 'viewport', content: 'width=device-width, initial-scale=1' }],
  link: [{ rel: 'icon', href: '/favicon.ico' }],
  htmlAttrs: { lang: 'it' }
})

useSeoMeta({ title: 'Smart CRM' })

const authStore = useAuthStore()
const chatStore = useChatStore()
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
        <NuxtLink to="/dashboard" class="font-semibold text-lg">Smart CRM</NuxtLink>
      </template>

      <template #right>
        <UButton icon="lucide:upload" variant="ghost" to="/import">Importa</UButton>
        <UButton icon="lucide:bot" variant="ghost" @click="chatStore.open = true">
          AI
        </UButton>
        <UColorModeButton />
        <UButton icon="lucide:log-out" variant="ghost" color="neutral" @click="logout" />
      </template>
    </UHeader>

    <UMain>
      <NuxtPage />
    </UMain>

    <!-- Chat AI sempre accessibile -->
    <AiChatSidebar />
  </UApp>
</template>
