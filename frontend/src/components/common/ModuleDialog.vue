<template>
	<Dialog v-model:open="open" :title="module ? 'Edit module' : 'New module'" size="lg">
		<template #default>
			<div class="space-y-3">
				<FormControl v-model="form.title" label="Title" placeholder="Checkout revamp" />
				<FormControl v-model="form.description" type="textarea" label="Description" />
				<div class="grid grid-cols-2 gap-3">
					<FormControl
						v-model="form.status"
						type="select"
						label="Status"
						:options="MODULE_STATUSES"
					/>
					<FormControl
						v-model="form.lead"
						type="select"
						label="Lead"
						:options="[{ label: 'None', value: '' }, ...memberOptions]"
					/>
					<div>
						<FormLabel label="Start date" />
						<DatePicker v-model="form.start_date" class="mt-1.5" />
					</div>
					<div>
						<FormLabel label="Target date" />
						<DatePicker v-model="form.target_date" class="mt-1.5" />
					</div>
				</div>
				<ErrorMessage :message="error" />
			</div>
		</template>
		<template #actions>
			<div class="flex justify-end gap-2">
				<Button label="Cancel" @click="open = false" />
				<Button
					variant="solid"
					:label="module ? 'Save' : 'Create'"
					:loading="saving"
					:disabled="!form.title"
					@click="save"
				/>
			</div>
		</template>
	</Dialog>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { Button, DatePicker, Dialog, ErrorMessage, FormControl, FormLabel } from 'frappe-ui'
import { api, errorMessage } from '@/api'
import { refreshProject, useWorkspace } from '@/stores/workspace'
import type { Module } from '@/types'
import { MODULE_STATUSES } from '@/utils/constants'

const props = defineProps<{ project: string; module?: Module | null }>()
const emit = defineEmits<{ saved: [] }>()
const open = defineModel<boolean>('open', { default: false })
const ws = useWorkspace()
const form = reactive({
	title: '',
	description: '',
	status: 'Backlog',
	lead: '',
	start_date: '',
	target_date: '',
})
const error = ref('')
const saving = ref(false)

const memberOptions = computed(() =>
	(ws.project(props.project)?.members ?? []).map((m) => ({
		label: m.full_name || m.user,
		value: m.user,
	})),
)

watch(open, (v) => {
	if (!v) return
	error.value = ''
	const m = props.module
	Object.assign(form, {
		title: m?.title ?? '',
		description: (m?.description ?? '').replace(/<[^>]+>/g, ''),
		status: m?.status ?? 'Backlog',
		lead: m?.lead ?? '',
		start_date: m?.start_date ?? '',
		target_date: m?.target_date ?? '',
	})
})

async function save() {
	saving.value = true
	error.value = ''
	const values = {
		...form,
		lead: form.lead || null,
		start_date: form.start_date || null,
		target_date: form.target_date || null,
	}
	try {
		if (props.module) await api.setValue('Runway Module', props.module.name, values)
		else await api.insert({ doctype: 'Runway Module', project: props.project, ...values })
		await refreshProject(props.project)
		open.value = false
		emit('saved')
	} catch (e) {
		error.value = errorMessage(e)
	} finally {
		saving.value = false
	}
}
</script>
