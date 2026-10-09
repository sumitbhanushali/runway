<template>
	<div class="flex min-h-0 flex-1 flex-col">
		<div class="flex flex-wrap items-center gap-2 border-b border-outline-gray-1 px-4 py-2">
			<TextInput
				v-model="search"
				size="sm"
				class="w-56"
				placeholder="Search work items"
				:debounce="250"
			>
				<template #prefix><span class="lucide-search size-3.5 text-ink-gray-5" /></template>
			</TextInput>
			<div class="ml-auto flex items-center gap-2">
				<slot name="toolbar" />
				<TabButtons v-model="view.display.layout" :options="layoutOptions" size="sm" />
				<FilterMenu v-model="view.filters" :project="project" :hide="hideFilters" />
				<DisplayMenu
					v-model:display="view.display"
					v-model:properties="view.properties"
					:layout="view.display.layout"
					:single-project="!!project"
				/>
				<Button
					v-if="canCreate"
					size="sm"
					variant="solid"
					icon-left="lucide-plus"
					label="Work item"
					@click="openCreate()"
				/>
			</div>
		</div>
		<AppliedFilters v-model="view.filters" :project="project" />

		<div v-if="store.loading.value && !store.loaded.value" class="space-y-2 p-4">
			<div v-for="i in 6" :key="i" class="h-9 animate-pulse rounded-3 bg-surface-gray-2" />
		</div>
		<EmptyState
			v-else-if="!store.items.value.length"
			icon="lucide-layers"
			:title="emptyTitle"
			:description="emptyDescription"
		>
			<Button
				v-if="canCreate"
				variant="solid"
				icon-left="lucide-plus"
				label="Create work item"
				@click="openCreate()"
			/>
		</EmptyState>
		<ListLayout
			v-else-if="view.display.layout === 'list'"
			:groups="groups"
			:group-by="effectiveGroupBy"
			:properties="view.properties"
			:editable="editable"
			:can-create="canQuickAdd"
			:project-identifier="projectDoc?.identifier"
			:selected="selected"
			:create="createWith"
			@open="openItem"
			@update="update"
			@create-in="(g) => openCreate(g.defaults)"
		/>
		<KanbanLayout
			v-else-if="view.display.layout === 'kanban'"
			:groups="groups"
			:group-by="effectiveGroupBy"
			:properties="view.properties"
			:editable="editable"
			:can-create="canQuickAdd"
			:project-identifier="projectDoc?.identifier"
			:create="createWith"
			@open="openItem"
			@update="update"
			@create-in="(g) => openCreate(g.defaults)"
		/>
		<SpreadsheetLayout
			v-else
			:items="store.items.value"
			:properties="view.properties"
			:editable="editable"
			:can-create="canQuickAdd"
			:project-identifier="projectDoc?.identifier"
			:create="createWith"
			@open="openItem"
			@update="update"
		/>
	</div>
</template>

<script setup lang="ts">
import { computed, onScopeDispose } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Button, TabButtons, TextInput } from 'frappe-ui'
import EmptyState from '@/components/common/EmptyState.vue'
import AppliedFilters from '@/components/filters/AppliedFilters.vue'
import DisplayMenu from '@/components/filters/DisplayMenu.vue'
import FilterMenu from '@/components/filters/FilterMenu.vue'
import KanbanLayout from '@/components/layouts/KanbanLayout.vue'
import ListLayout from '@/components/layouts/ListLayout.vue'
import SpreadsheetLayout from '@/components/layouts/SpreadsheetLayout.vue'
import type { DisplayState } from '@/composables/useDisplay'
import { useWorkItems, type ItemsQuery } from '@/composables/useWorkItems'
import { useWorkspace } from '@/stores/workspace'
import type { WorkItem } from '@/types'
import { bus } from '@/utils/bus'
import { groupItems } from '@/utils/grouping'

const props = withDefaults(
	defineProps<{
		state: DisplayState
		project?: string | null
		cycle?: string
		module?: string
		view?: string
		myWork?: string
		/** Values every item created here starts with (e.g. the cycle being viewed). */
		defaults?: Partial<WorkItem>
		hideFilters?: string[]
		emptyTitle?: string
		emptyDescription?: string
	}>(),
	{
		emptyTitle: 'No work items',
		emptyDescription: 'Work items matching this view will show up here.',
	},
)

// The display state is a reactive store owned by the page (and persisted per
// scope); the board edits it in place rather than round-tripping via events.
const view = props.state

const ws = useWorkspace()
const route = useRoute()
const router = useRouter()

const projectDoc = computed(() => ws.project(props.project))
const canCreate = computed(() =>
	projectDoc.value
		? projectDoc.value.role !== 'Guest'
		: ws.projects.value.some((p) => p.role !== 'Guest'),
)
const canQuickAdd = computed(() => !!projectDoc.value && projectDoc.value.role !== 'Guest')

const search = computed({
	get: () => view.filters.search ?? '',
	set: (v: string) => (view.filters.search = v || undefined),
})

const query = computed<ItemsQuery | null>(() => {
	if (!ws.workspace.value) return null
	return {
		project: props.project ?? undefined,
		workspace: props.project ? undefined : ws.workspace.value,
		cycle: props.cycle,
		module: props.module,
		view: props.view,
		myWork: props.myWork,
		filters: view.filters,
		order_by: view.display.order_by,
		show_sub_items: view.display.show_sub_items,
	}
})
const store = useWorkItems(query)
defineExpose({ reload: store.reload })

const effectiveGroupBy = computed(() => {
	const g = view.display.group_by
	if (view.display.layout === 'kanban' && g === 'none') return 'state_group'
	if (!projectDoc.value && g === 'state') return 'state_group'
	return g
})
const groups = computed(() =>
	groupItems(store.items.value, effectiveGroupBy.value, {
		project: projectDoc.value,
		userName: ws.userName,
		showEmpty: view.display.show_empty_groups,
	}),
)

const layoutOptions = [
	{ value: 'list', icon: 'lucide-list', tooltip: 'List' },
	{ value: 'kanban', icon: 'lucide-columns-3', tooltip: 'Board' },
	{ value: 'spreadsheet', icon: 'lucide-sheet', tooltip: 'Spreadsheet' },
]

const selected = computed(() => (route.query.peek as string) || null)

function editable(item: WorkItem) {
	const p = ws.project(item.project)
	return !!p && p.role !== 'Guest'
}

function openItem(item: WorkItem) {
	router.push({ query: { ...route.query, peek: item.name } })
}

async function update(name: string, values: Partial<WorkItem>) {
	const row = await store.update(name, values)
	bus.emit('item-updated', row)
}

async function createWith(defaults: Partial<WorkItem>, title: string) {
	if (!props.project) return
	const row = await store.create(props.project, { ...props.defaults, ...defaults, title })
	bus.emit('item-created', row)
	return row
}

function openCreate(defaults: Partial<WorkItem> = {}) {
	bus.emit('create-item', {
		project: props.project ?? undefined,
		defaults: { ...props.defaults, ...defaults },
	})
}

// Keep this board in step with edits made in the peek or the create dialog.
const offs = [
	bus.on('item-updated', (row) => {
		if (store.items.value.some((i) => i.name === row.name)) store.replace(row)
	}),
	bus.on('item-created', () => store.reload()),
	bus.on('item-deleted', (name) => store.remove(name)),
]
onScopeDispose(() => offs.forEach((off) => off()))
</script>
