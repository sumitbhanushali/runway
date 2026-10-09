<template>
	<Dialog v-model:open="open" size="2xl" title="New work item">
		<template #default>
			<div class="space-y-3">
				<div class="flex items-center gap-2">
					<OptionPicker
						v-model="project"
						:options="projectOptions"
						bordered
						placeholder="Project"
						search-placeholder="Pick a project…"
					/>
					<span v-if="parentTitle" class="truncate text-sm text-ink-gray-5"
						>Sub-item of {{ parentTitle }}</span
					>
				</div>
				<input
					ref="titleEl"
					v-model="draft.title"
					class="w-full border-0 bg-transparent px-0 text-xl font-medium text-ink-gray-9 placeholder-ink-gray-4 focus:ring-0"
					placeholder="Title"
					@keydown.meta.enter="submit"
					@keydown.ctrl.enter="submit"
				/>
				<RichEditor
					v-model="draft.description"
					kit="rich"
					placeholder="Add a description…"
					content-class="min-h-32 max-h-80 overflow-y-auto px-3 py-2"
				/>
				<div v-if="project && previewItem" class="flex flex-wrap items-center gap-1.5">
					<ItemProperty
						v-for="prop in PROPS"
						:key="prop"
						:item="previewItem"
						:prop="prop"
						bordered
						@update="(v) => Object.assign(draft, v)"
					/>
				</div>
			</div>
		</template>
		<template #actions>
			<div class="flex items-center justify-between gap-2">
				<Switch v-model="createMore" label="Create more" size="sm" />
				<div class="flex gap-2">
					<Button label="Cancel" @click="open = false" />
					<Button
						variant="solid"
						label="Create"
						:loading="saving"
						:disabled="!draft.title.trim() || !project"
						@click="submit"
					/>
				</div>
			</div>
		</template>
	</Dialog>
</template>

<script setup lang="ts">
import { computed, nextTick, onScopeDispose, reactive, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Button, Dialog, Switch, toast } from 'frappe-ui'
import RichEditor from '@/components/common/RichEditor.vue'
import OptionPicker from '@/components/pickers/OptionPicker.vue'
import ItemProperty from './ItemProperty.vue'
import { api, errorMessage } from '@/api'
import { useWorkspace } from '@/stores/workspace'
import type { WorkItem } from '@/types'
import { bus } from '@/utils/bus'

const PROPS = [
	'state',
	'priority',
	'assignees',
	'labels',
	'start_date',
	'due_date',
	'estimate',
	'cycle',
	'modules',
]

const ws = useWorkspace()
const router = useRouter()
const route = useRoute()
const open = ref(false)
const saving = ref(false)
const createMore = ref(false)
const project = ref<string | null>(null)
const titleEl = ref<HTMLInputElement | null>(null)

type Draft = Partial<WorkItem> & { title: string; description: string }
const blank = (): Draft => ({
	title: '',
	description: '',
	priority: 'None',
	assignees: [],
	labels: [],
	modules: [],
})
const draft = reactive<Draft>(blank())

const projectOptions = computed(() =>
	ws.projects.value
		.filter((p) => p.role !== 'Guest')
		.map((p) => ({
			value: p.name,
			label: p.title,
			emoji: p.emoji || undefined,
			icon: p.emoji ? undefined : 'lucide-folder',
		})),
)

const parentTitle = computed(() => draft.parent_item || '')

// ItemProperty edits a WorkItem; give it a stand-in built from the draft.
const previewItem = computed<WorkItem | null>(() => {
	const p = ws.project(project.value)
	if (!p) return null
	const state = draft.state || p.states.find((s) => s.is_default)?.name || p.states[0]?.name
	return {
		name: 'new',
		project: p.name,
		sequence_id: 0,
		title: draft.title,
		state: state!,
		state_group: p.states.find((s) => s.name === state)?.state_group ?? 'Backlog',
		priority: draft.priority ?? 'None',
		start_date: draft.start_date ?? null,
		due_date: draft.due_date ?? null,
		estimate_point: draft.estimate_point ?? null,
		cycle: draft.cycle ?? null,
		parent_item: draft.parent_item ?? null,
		sort_order: 0,
		is_draft: 0,
		archived_at: null,
		completed_at: null,
		owner: '',
		creation: '',
		modified: '',
		assignees: draft.assignees ?? [],
		labels: draft.labels ?? [],
		modules: draft.modules ?? [],
		sub_items_count: 0,
		sub_items_done: 0,
		link_count: 0,
		attachment_count: 0,
	}
})

const off = bus.on('create-item', async ({ project: p, defaults }) => {
	Object.assign(draft, blank(), defaults ?? {})
	project.value = p ?? (route.params.project as string) ?? projectOptions.value[0]?.value ?? null
	open.value = true
	await nextTick()
	titleEl.value?.focus()
})
onScopeDispose(off)

async function submit() {
	if (!project.value || !draft.title.trim()) return
	saving.value = true
	try {
		const values: Record<string, unknown> = { ...draft, title: draft.title.trim() }
		const row = await api.createItem(project.value, values)
		bus.emit('item-created', row)
		toast.success(`${row.name} created`)
		if (createMore.value) {
			Object.assign(draft, { title: '', description: '' })
			titleEl.value?.focus()
		} else {
			open.value = false
			router.push({ query: { ...route.query, peek: row.name } })
		}
	} catch (e) {
		toast.error(errorMessage(e))
	} finally {
		saving.value = false
	}
}
</script>
