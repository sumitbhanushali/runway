<template>
	<div class="flex-1 overflow-auto">
		<table class="min-w-full border-separate border-spacing-0 text-sm">
			<thead class="sticky top-0 z-[1] bg-surface-gray-1">
				<tr>
					<th
						v-for="col in columns"
						:key="col.key"
						class="whitespace-nowrap border-b border-r border-outline-gray-1 px-3 py-2 text-left font-medium text-ink-gray-6"
						:class="
							col.key === 'title'
								? 'sticky left-0 z-[2] min-w-80 bg-surface-gray-1'
								: ''
						"
					>
						{{ col.label }}
					</th>
				</tr>
			</thead>
			<tbody>
				<tr
					v-for="item in items"
					:key="item.name"
					class="group/row hover:bg-surface-gray-1"
				>
					<td
						v-for="col in columns"
						:key="col.key"
						class="h-10 whitespace-nowrap border-b border-r border-outline-gray-1 px-2"
						:class="
							col.key === 'title'
								? 'sticky left-0 bg-surface-base group-hover/row:bg-surface-gray-1'
								: ''
						"
					>
						<button
							v-if="col.key === 'title'"
							type="button"
							class="flex w-full items-center gap-2 text-left"
							@click="emit('open', item)"
						>
							<span class="w-16 shrink-0 text-ink-gray-5">{{ item.name }}</span>
							<span class="truncate text-ink-gray-9">{{ item.title }}</span>
						</button>
						<ItemProperty
							v-else-if="EDITABLE.includes(col.key)"
							:item="item"
							:prop="col.key"
							:editable="editable(item)"
							@update="(v) => emit('update', item.name, v)"
						/>
						<span v-else-if="col.key === 'sub_items'" class="px-1 text-ink-gray-6">
							{{
								item.sub_items_count
									? `${item.sub_items_done}/${item.sub_items_count}`
									: '—'
							}}
						</span>
						<span
							v-else-if="col.key === 'creation' || col.key === 'modified'"
							class="px-1 text-ink-gray-6"
						>
							{{ dayjs(item[col.key]).format('MMM D, YYYY') }}
						</span>
					</td>
				</tr>
			</tbody>
		</table>
		<QuickAdd
			v-if="canCreate"
			:project-identifier="projectIdentifier"
			:create="(t: string) => create({}, t)"
			form-class="border-b border-outline-gray-1"
		/>
	</div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { dayjs } from 'frappe-ui'
import QuickAdd from './QuickAdd.vue'
import ItemProperty from '@/components/workitem/ItemProperty.vue'
import type { DisplayProperty, WorkItem } from '@/types'

const EDITABLE = [
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
const ALL = [
	{ key: 'title', label: 'Work item' },
	{ key: 'state', label: 'State' },
	{ key: 'priority', label: 'Priority' },
	{ key: 'assignees', label: 'Assignees' },
	{ key: 'labels', label: 'Labels' },
	{ key: 'start_date', label: 'Start date' },
	{ key: 'due_date', label: 'Due date' },
	{ key: 'estimate', label: 'Estimate' },
	{ key: 'cycle', label: 'Cycle' },
	{ key: 'modules', label: 'Modules' },
	{ key: 'sub_items', label: 'Sub-items' },
	{ key: 'creation', label: 'Created' },
	{ key: 'modified', label: 'Updated' },
] as const

const props = defineProps<{
	items: WorkItem[]
	properties: DisplayProperty[]
	editable: (item: WorkItem) => boolean
	canCreate: boolean
	projectIdentifier?: string
	create: (defaults: Partial<WorkItem>, title: string) => Promise<unknown>
}>()
const emit = defineEmits<{
	open: [item: WorkItem]
	update: [name: string, values: Partial<WorkItem>]
}>()

const columns = computed(() =>
	ALL.filter(
		(c) =>
			c.key === 'title' ||
			c.key === 'creation' ||
			c.key === 'modified' ||
			props.properties.includes(c.key as DisplayProperty),
	),
)
</script>
