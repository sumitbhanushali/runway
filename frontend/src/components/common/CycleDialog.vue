<template>
	<Dialog v-model:open="open" :title="cycle ? 'Edit cycle' : 'New cycle'" size="lg">
		<template #default>
			<div class="space-y-3">
				<FormControl v-model="form.title" label="Title" placeholder="Sprint 12" />
				<FormControl v-model="form.description" type="textarea" label="Description" />
				<div class="grid grid-cols-2 gap-3">
					<div>
						<FormLabel label="Start date" />
						<DatePicker v-model="form.start_date" class="mt-1.5" placeholder="Start" />
					</div>
					<div>
						<FormLabel label="End date" />
						<DatePicker v-model="form.end_date" class="mt-1.5" placeholder="End" />
					</div>
				</div>
				<p class="text-xs text-ink-gray-5">
					Cycles in a project cannot overlap. Leave dates empty to keep it as a draft.
				</p>
				<ErrorMessage :message="error" />
			</div>
		</template>
		<template #actions>
			<div class="flex justify-end gap-2">
				<Button label="Cancel" @click="open = false" />
				<Button
					variant="solid"
					:label="cycle ? 'Save' : 'Create'"
					:loading="saving"
					:disabled="!form.title"
					@click="save"
				/>
			</div>
		</template>
	</Dialog>
</template>

<script setup lang="ts">
import { reactive, ref, watch } from 'vue'
import { Button, DatePicker, Dialog, ErrorMessage, FormControl, FormLabel } from 'frappe-ui'
import { api, errorMessage } from '@/api'
import { refreshProject } from '@/stores/workspace'
import type { Cycle } from '@/types'

const props = defineProps<{ project: string; cycle?: Cycle | null }>()
const emit = defineEmits<{ saved: [] }>()
const open = defineModel<boolean>('open', { default: false })
const form = reactive({ title: '', description: '', start_date: '', end_date: '' })
const error = ref('')
const saving = ref(false)

watch(open, (v) => {
	if (!v) return
	error.value = ''
	Object.assign(form, {
		title: props.cycle?.title ?? '',
		description: props.cycle?.description ?? '',
		start_date: props.cycle?.start_date ?? '',
		end_date: props.cycle?.end_date ?? '',
	})
})

async function save() {
	saving.value = true
	error.value = ''
	const values = { ...form, start_date: form.start_date || null, end_date: form.end_date || null }
	try {
		if (props.cycle) await api.setValue('Runway Cycle', props.cycle.name, values)
		else await api.insert({ doctype: 'Runway Cycle', project: props.project, ...values })
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
