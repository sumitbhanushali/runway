<template>
	<div class="flex flex-1 gap-3 overflow-x-auto p-4">
		<section
			v-for="group in groups"
			:key="group.key"
			class="flex w-72 shrink-0 flex-col rounded-5 bg-surface-gray-1"
			:class="{ 'ring-2 ring-outline-gray-4': dragOver === group.key }"
			@dragover.prevent="onDragOver(group, $event)"
			@dragleave="dragOver = null"
			@drop.prevent="onDrop(group)"
		>
			<header class="flex h-10 items-center gap-2 px-3">
				<GroupMark :group="group" />
				<span class="truncate text-sm font-medium text-ink-gray-8">{{ group.label }}</span>
				<span class="text-sm text-ink-gray-5">{{ group.items.length }}</span>
				<button
					v-if="canCreate"
					type="button"
					class="ml-auto rounded-3 p-1 text-ink-gray-5 hover:bg-surface-gray-3"
					@click="emit('create-in', group)"
				>
					<span class="lucide-plus block size-4" />
				</button>
			</header>
			<div class="flex min-h-16 flex-1 flex-col gap-2 overflow-y-auto px-2 pb-2">
				<article
					v-for="item in group.items"
					:key="item.name"
					:draggable="editable(item)"
					class="cursor-pointer rounded-4 border border-outline-gray-1 bg-surface-base p-2.5 shadow-sm hover:border-outline-gray-3"
					:class="{
						'opacity-40': dragging?.item.name === item.name,
						'border-t-2 border-t-outline-gray-5':
							dropBefore === item.name && dragOver === group.key,
					}"
					@dragstart="onDragStart(item, group, $event)"
					@dragend="reset"
					@dragover.prevent.stop="onCardOver(group, item)"
					@click="emit('open', item)"
				>
					<div v-if="properties.includes('id')" class="mb-1 text-xs text-ink-gray-5">
						{{ item.name }}
					</div>
					<div class="mb-2 line-clamp-3 text-sm text-ink-gray-9">{{ item.title }}</div>
					<ItemProperties
						:item="item"
						:properties="properties"
						:editable="editable(item)"
						compact
						:hide="[groupBy]"
						@update="(v) => emit('update', item.name, v)"
					/>
				</article>
				<QuickAdd
					v-if="canCreate"
					:project-identifier="projectIdentifier"
					:create="(t: string) => create(group.defaults, t)"
					button-class="px-2"
					form-class="rounded-4 bg-surface-base px-2"
				/>
			</div>
		</section>
	</div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import GroupMark from './GroupMark.vue'
import ItemProperties from './ItemProperties.vue'
import QuickAdd from './QuickAdd.vue'
import type { DisplayProperty, GroupBy, WorkItem } from '@/types'
import type { ItemGroup } from '@/utils/grouping'

const props = defineProps<{
	groups: ItemGroup[]
	groupBy: GroupBy
	properties: DisplayProperty[]
	editable: (item: WorkItem) => boolean
	canCreate: boolean
	projectIdentifier?: string
	create: (defaults: Partial<WorkItem>, title: string) => Promise<unknown>
}>()
const emit = defineEmits<{
	open: [item: WorkItem]
	update: [name: string, values: Partial<WorkItem>]
	'create-in': [group: ItemGroup]
}>()

const dragging = ref<{ item: WorkItem; from: ItemGroup } | null>(null)
const dragOver = ref<string | null>(null)
const dropBefore = ref<string | null>(null)

function onDragStart(item: WorkItem, group: ItemGroup, e: DragEvent) {
	dragging.value = { item, from: group }
	e.dataTransfer?.setData('text/plain', item.name)
	if (e.dataTransfer) e.dataTransfer.effectAllowed = 'move'
}

function onDragOver(group: ItemGroup, e: DragEvent) {
	if (!dragging.value) return
	dragOver.value = group.key
	// Hovering the column's empty tail means "drop at the end".
	if (e.target === e.currentTarget) dropBefore.value = null
}

function onCardOver(group: ItemGroup, item: WorkItem) {
	if (!dragging.value) return
	dragOver.value = group.key
	dropBefore.value = item.name === dragging.value.item.name ? null : item.name
}

function reset() {
	dragging.value = null
	dragOver.value = null
	dropBefore.value = null
}

const MULTI: GroupBy[] = ['assignees', 'labels', 'modules']

function onDrop(target: ItemGroup) {
	const drag = dragging.value
	const before = dropBefore.value
	reset()
	if (!drag) return
	const { item, from } = drag
	const values: Partial<WorkItem> = {}

	if (target.key !== from.key && props.groupBy !== 'state_group' && props.groupBy !== 'none') {
		if (MULTI.includes(props.groupBy)) {
			const field = props.groupBy as 'assignees' | 'labels' | 'modules'
			const next = item[field].filter((v) => v !== from.key)
			if (target.key !== '__none__') next.push(target.key)
			values[field] = [...new Set(next)]
		} else if (props.groupBy === 'cycle') {
			values.cycle = target.key === '__none__' ? null : target.key
		} else {
			Object.assign(values, target.defaults)
		}
	}

	// Manual order: land between the neighbours around the drop point.
	const list = target.items.filter((i) => i.name !== item.name)
	const idx = before ? list.findIndex((i) => i.name === before) : list.length
	const prev = list[idx - 1]?.sort_order
	const next = list[idx]?.sort_order
	if (prev !== undefined && next !== undefined) values.sort_order = (prev + next) / 2
	else if (next !== undefined) values.sort_order = next - 1
	else if (prev !== undefined) values.sort_order = prev + 1

	if (Object.keys(values).length) emit('update', item.name, values)
}
</script>
