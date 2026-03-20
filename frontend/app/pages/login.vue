<script setup lang="ts">
definePageMeta({ layout: false })

const authStore = useAuthStore()
const toast = useToast()
const router = useRouter()

const form = reactive({ username: '', password: '' })
const loading = ref(false)

async function onSubmit() {
  loading.value = true
  try {
    await authStore.login(form.username, form.password)
    router.push('/dashboard')
  } catch (e: any) {
    toast.add({ title: e.message, color: 'error' })
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-950">
    <UCard class="w-full max-w-sm">
      <template #header>
        <div class="flex justify-center py-2">
          <svg width="240" height="114" viewBox="20 20 170 80" xmlns="http://www.w3.org/2000/svg">
            <g transform="translate(25,30)">
              <circle cx="30" cy="30" r="22" stroke="#22c55e" stroke-width="2" fill="none"/>
              <circle cx="30" cy="30" r="4" fill="#22c55e"/>
              <circle cx="30" cy="8" r="3" fill="#22c55e"/>
              <circle cx="52" cy="30" r="3" fill="#22c55e"/>
              <circle cx="30" cy="52" r="3" fill="#22c55e"/>
              <circle cx="8" cy="30" r="3" fill="#22c55e"/>
              <line x1="30" y1="30" x2="30" y2="8" stroke="#22c55e" stroke-width="1.5" opacity="0.7"/>
              <line x1="30" y1="30" x2="52" y2="30" stroke="#22c55e" stroke-width="1.5" opacity="0.7"/>
              <line x1="30" y1="30" x2="30" y2="52" stroke="#22c55e" stroke-width="1.5" opacity="0.7"/>
              <line x1="30" y1="30" x2="8" y2="30" stroke="#22c55e" stroke-width="1.5" opacity="0.7"/>
            </g>
            <text x="100" y="58" font-family="Inter, Arial, sans-serif" font-size="28" class="fill-gray-800 dark:fill-gray-200">Smart</text>
            <text x="100" y="88" font-family="Inter, Arial, sans-serif" font-size="28" font-weight="600" fill="#22c55e">CRM</text>
          </svg>
        </div>
      </template>

      <UForm :state="form" @submit="onSubmit" class="flex flex-col gap-4">
        <UFormField label="Username" name="username">
          <UInput v-model="form.username" placeholder="username" />
        </UFormField>

        <UFormField label="Password" name="password">
          <UInput v-model="form.password" type="password" placeholder="••••••••" />
        </UFormField>

        <UButton type="submit" :loading="loading" block>
          Accedi
        </UButton>
      </UForm>
    </UCard>
  </div>
</template>
