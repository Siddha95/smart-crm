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
        <h1 class="text-xl font-semibold text-center">Smart CRM</h1>
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
