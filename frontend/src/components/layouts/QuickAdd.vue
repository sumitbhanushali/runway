<template>
	<div v-if="!active">
		<button
			type="button"
			class="flex w-full items-center gap-2 px-4 py-2 text-sm text-ink-gray-5 hover:text-ink-gray-8"
			:class="buttonClass"
			@click="start"
		>
			<span class="lucide-plus size-4" /> New work item
		</button>
	</div>
	<form
		v-else
		class="flex items-center gap-2 px-4 py-1.5"
		:class="formClass"
		@submit.prevent="submit"
	>
		<span class="text-xs text-ink-gray-4">{{ projectIdentifier }}</span>
		<input
			ref="input"
			v-model="title"
			class="h-7 flex-1 border-0 bg-transparent px-0 text-sm text-ink-gray-9 placeholder-ink-gray-4 focus:ring-0"
			placeholder="Work item title — press Enter to add, Esc to close"
			@keydown.esc="active = false"
			@blur="!title && (active = false)"
		/>
		<Button size="sm" type="submit" variant="solid" :loading="saving" label="Add" />
	</form>
</template>

<script setup lang="ts">
import { nextTick, ref } from 'vue'
import { Button } from 'frappe-ui'

const props = defineProps<{
	projectIdentifier?: string
	create: (title: string) => Promise<unknown>
	buttonClass?: string
	formClass?: string
}>()

const active = ref(false)
const title = ref('')
const saving = ref(false)
const input = ref<HTMLInputElement | null>(null)

async function start() {
	active.value = true
	await nextTick()
	input.value?.focus()
}

async function submit() {
	const t = title.value.trim()
	if (!t) return
	saving.value = true
	try {
		await props.create(t)
		title.value = ''
		await nextTick()
		input.value?.focus()
	} finally {
		saving.value = false
	}
}
</script>
