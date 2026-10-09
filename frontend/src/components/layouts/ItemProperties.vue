<template>
	<div class="flex flex-wrap items-center gap-1" @click.stop>
		<template v-for="prop in visible" :key="prop">
			<ItemProperty
				v-if="EDITABLE.includes(prop)"
				:item="item"
				:prop="prop"
				:editable="editable"
				:compact="compact"
				:bordered="!compact"
				@update="(v) => emit('update', v)"
			/>
			<Tooltip
				v-else-if="prop === 'sub_items' && item.sub_items_count"
				text="Sub-work items done"
			>
				<span
					class="flex h-6 items-center gap-1 rounded-3 border border-outline-gray-2 px-1.5 text-xs text-ink-gray-6"
				>
					<span class="lucide-git-branch size-3.5" />{{ item.sub_items_done }}/{{
						item.sub_items_count
					}}
				</span>
			</Tooltip>
			<span
				v-else-if="prop === 'links' && item.link_count"
				class="flex h-6 items-center gap-1 rounded-3 border border-outline-gray-2 px-1.5 text-xs text-ink-gray-6"
			>
				<span class="lucide-link size-3.5" />{{ item.link_count }}
			</span>
			<span
				v-else-if="prop === 'attachments' && item.attachment_count"
				class="flex h-6 items-center gap-1 rounded-3 border border-outline-gray-2 px-1.5 text-xs text-ink-gray-6"
			>
				<span class="lucide-paperclip size-3.5" />{{ item.attachment_count }}
			</span>
		</template>
	</div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Tooltip } from 'frappe-ui'
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

const props = withDefaults(
	defineProps<{
		item: WorkItem
		properties: DisplayProperty[]
		editable?: boolean
		compact?: boolean
		/** Properties already conveyed by the layout (e.g. state in a state-grouped board). */
		hide?: string[]
	}>(),
	{ editable: true, compact: false, hide: () => [] },
)
const emit = defineEmits<{ update: [values: Partial<WorkItem>] }>()

const visible = computed(() =>
	props.properties.filter(
		(p) =>
			p !== 'id' &&
			!props.hide.includes(p) &&
			!(p === 'state' && props.hide.includes('state')),
	),
)
</script>
