<template>
	<Dialog v-model:open="open" :title="view ? 'Update view' : 'Save view'" size="md">
		<template #default>
			<div class="space-y-3">
				<FormControl v-model="title" label="Name" placeholder="My urgent bugs" />
				<FormControl v-model="description" type="textarea" label="Description" />
				<FormControl
					v-model="access"
					type="select"
					label="Visibility"
					:options="[
						{ label: 'Private — only you', value: 'Private' },
						{ label: 'Public — everyone with access', value: 'Public' },
					]"
				/>
				<p class="text-sm text-ink-gray-5">
					The current filters, layout and display properties are saved with the view.
				</p>
			</div>
		</template>
		<template #actions>
			<div class="flex justify-end gap-2">
				<Button label="Cancel" @click="open = false" />
				<Button
					variant="solid"
					:label="view ? 'Update' : 'Save'"
					:loading="saving"
					:disabled="!title"
					@click="save"
				/>
			</div>
		</template>
	</Dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Button, Dialog, FormControl, toast } from 'frappe-ui'
import { api, errorMessage } from '@/api'
import type { DisplayState } from '@/composables/useDisplay'
import { useWorkspace } from '@/stores/workspace'
import type { SavedView } from '@/types'

const props = defineProps<{
	project?: string | null
	state: DisplayState
	view?: SavedView | null
}>()
const emit = defineEmits<{ saved: [view: SavedView] }>()
const open = defineModel<boolean>('open', { default: false })

const ws = useWorkspace()
const router = useRouter()
const title = ref('')
const description = ref('')
const access = ref<'Private' | 'Public'>('Private')
const saving = ref(false)

watch(open, (v) => {
	if (!v) return
	title.value = props.view?.title ?? ''
	description.value = props.view?.description ?? ''
	access.value = props.view?.access ?? 'Private'
})

async function save() {
	saving.value = true
	const { search: _search, ...filters } = props.state.filters
	void _search
	const values = {
		title: title.value,
		description: description.value,
		access: access.value,
		filters: JSON.stringify(filters),
		display_filters: JSON.stringify(props.state.display),
		display_properties: JSON.stringify(props.state.properties),
	}
	try {
		let doc: SavedView
		if (props.view) {
			doc = await api.setValue<SavedView>('Runway View', props.view.name, values)
		} else {
			doc = await api.insert<SavedView>({
				doctype: 'Runway View',
				workspace: ws.workspace.value,
				project: props.project || null,
				...values,
			})
			router.push(
				props.project
					? { name: 'ProjectView', params: { project: props.project, view: doc.name } }
					: { name: 'WorkspaceView', params: { view: doc.name } },
			)
		}
		toast.success('View saved')
		emit('saved', doc)
		open.value = false
	} catch (e) {
		toast.error(errorMessage(e))
	} finally {
		saving.value = false
	}
}
</script>
