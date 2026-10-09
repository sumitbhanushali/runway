<template>
	<div class="flex h-full items-center justify-center bg-surface-gray-1 p-6">
		<form
			class="w-full max-w-md space-y-4 rounded-6 bg-surface-base p-8 shadow-lg"
			@submit.prevent="create"
		>
			<img :src="logo" class="size-10" alt="" />
			<div>
				<h1 class="text-xl font-semibold text-ink-gray-9">Create a workspace</h1>
				<p class="mt-1 text-p-base text-ink-gray-5">
					Workspaces hold your team's projects, members and views.
				</p>
			</div>
			<FormControl v-model="title" label="Workspace name" placeholder="Acme Inc." required />
			<FormControl v-model="slug" label="Workspace URL" placeholder="acme">
				<template #prefix><span class="text-sm text-ink-gray-5">/runway/</span></template>
			</FormControl>
			<ErrorMessage :message="error" />
			<Button
				class="w-full"
				variant="solid"
				type="submit"
				label="Create workspace"
				:loading="saving"
				:disabled="!title || !slug"
			/>
			<Button
				v-if="hasWorkspaces"
				class="w-full"
				variant="ghost"
				label="Back"
				@click="router.back()"
			/>
		</form>
	</div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Button, ErrorMessage, FormControl } from 'frappe-ui'
import { api, errorMessage } from '@/api'
import { loadBoot, useWorkspace } from '@/stores/workspace'

const router = useRouter()
const logo = '/assets/runway/images/runway-logo.svg'
const ws = useWorkspace()
const title = ref('')
const slug = ref('')
const error = ref('')
const saving = ref(false)
let slugEdited = false

const hasWorkspaces = computed(() => !!ws.boot.value?.workspaces.length)

watch(title, (t) => {
	if (!slugEdited)
		slug.value = t
			.toLowerCase()
			.replace(/[^a-z0-9]+/g, '-')
			.replace(/^-|-$/g, '')
			.slice(0, 48)
})
watch(slug, (s, old) => {
	if (
		old !== undefined &&
		s !==
			title.value
				.toLowerCase()
				.replace(/[^a-z0-9]+/g, '-')
				.replace(/^-|-$/g, '')
				.slice(0, 48)
	)
		slugEdited = true
})

async function create() {
	saving.value = true
	error.value = ''
	try {
		const name = await api.createWorkspace(title.value, slug.value)
		await loadBoot(name, true)
		router.push({ name: 'Projects', params: { workspace: name }, query: { create: '1' } })
	} catch (e) {
		error.value = errorMessage(e)
	} finally {
		saving.value = false
	}
}
</script>
