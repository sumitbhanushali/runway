<template>
	<OptionPicker
		v-if="prop === 'state'"
		:model-value="item.state"
		:options="stateOptions"
		:disabled="!editable"
		:bordered="bordered"
		search-placeholder="Change state…"
		@change="(v) => set({ state: v as string })"
	>
		<template v-if="compact" #value="{ selected }">
			<OptionMark v-if="selected[0]" :option="selected[0]" />
		</template>
	</OptionPicker>

	<OptionPicker
		v-else-if="prop === 'priority'"
		:model-value="item.priority"
		:options="opts.priorities.value"
		:disabled="!editable"
		:bordered="bordered"
		:searchable="false"
		@change="(v) => set({ priority: v as Priority })"
	>
		<template v-if="compact" #value>
			<PriorityIcon :priority="item.priority" small />
		</template>
	</OptionPicker>

	<OptionPicker
		v-else-if="prop === 'assignees'"
		:model-value="item.assignees"
		:options="opts.members.value"
		multiple
		clearable
		:disabled="!editable"
		:bordered="bordered"
		placeholder="Assignees"
		placeholder-icon="lucide-users"
		@change="(v) => set({ assignees: v as string[] })"
	>
		<template #value>
			<AvatarGroup v-if="item.assignees.length" :users="item.assignees" />
			<template v-else>
				<span class="lucide-user-plus size-3.5 text-ink-gray-4" />
				<span v-if="!compact" class="text-ink-gray-4">Assignees</span>
			</template>
		</template>
	</OptionPicker>

	<OptionPicker
		v-else-if="prop === 'labels'"
		:model-value="item.labels"
		:options="opts.labels.value"
		multiple
		clearable
		:disabled="!editable"
		:bordered="bordered"
		placeholder="Labels"
		placeholder-icon="lucide-tag"
		@change="(v) => set({ labels: v as string[] })"
	>
		<template #value>
			<template v-if="item.labels.length">
				<span
					v-for="l in item.labels.slice(0, compact ? 2 : 6)"
					:key="l"
					class="flex items-center gap-1 rounded-full border border-outline-gray-2 px-1.5 text-xs text-ink-gray-7"
				>
					<span
						class="size-2 rounded-full"
						:style="{ background: opts.labelOf(l)?.color || '#999' }"
					/>
					{{ opts.labelOf(l)?.title }}
				</span>
				<span v-if="compact && item.labels.length > 2" class="text-xs text-ink-gray-5">
					+{{ item.labels.length - 2 }}
				</span>
			</template>
			<template v-else>
				<span class="lucide-tag size-3.5 text-ink-gray-4" />
				<span v-if="!compact" class="text-ink-gray-4">Labels</span>
			</template>
		</template>
	</OptionPicker>

	<DateChip
		v-else-if="prop === 'start_date'"
		:model-value="item.start_date"
		placeholder="Start date"
		icon="lucide-calendar-clock"
		:disabled="!editable"
		:bordered="bordered"
		@update:model-value="(v) => set({ start_date: v })"
	/>

	<DateChip
		v-else-if="prop === 'due_date'"
		:model-value="item.due_date"
		placeholder="Due date"
		icon="lucide-calendar-check-2"
		:warn-past="item.state_group !== 'Completed' && item.state_group !== 'Cancelled'"
		:disabled="!editable"
		:bordered="bordered"
		@update:model-value="(v) => set({ due_date: v })"
	/>

	<OptionPicker
		v-else-if="prop === 'estimate' && opts.estimates.value.length"
		:model-value="item.estimate_point"
		:options="opts.estimates.value"
		clearable
		:searchable="false"
		:disabled="!editable"
		:bordered="bordered"
		placeholder="Estimate"
		placeholder-icon="lucide-triangle"
		@change="(v) => set({ estimate_point: v as string | null })"
	/>

	<OptionPicker
		v-else-if="prop === 'cycle' && opts.project.value?.cycles_enabled"
		:model-value="item.cycle"
		:options="cycleOptions"
		clearable
		:disabled="!editable"
		:bordered="bordered"
		placeholder="Cycle"
		placeholder-icon="lucide-refresh-ccw"
		@change="(v) => set({ cycle: v as string | null })"
	/>

	<OptionPicker
		v-else-if="prop === 'modules' && opts.project.value?.modules_enabled"
		:model-value="item.modules"
		:options="opts.modules.value"
		multiple
		clearable
		:disabled="!editable"
		:bordered="bordered"
		placeholder="Modules"
		placeholder-icon="lucide-boxes"
		@change="(v) => set({ modules: v as string[] })"
	/>
</template>

<script setup lang="ts">
import { computed, toRef } from 'vue'
import AvatarGroup from '@/components/common/AvatarGroup.vue'
import PriorityIcon from '@/components/common/PriorityIcon.vue'
import DateChip from '@/components/pickers/DateChip.vue'
import OptionMark from '@/components/pickers/OptionMark.vue'
import OptionPicker from '@/components/pickers/OptionPicker.vue'
import { useProjectOptions } from '@/composables/useProjectOptions'
import type { Priority, WorkItem } from '@/types'

const props = withDefaults(
	defineProps<{
		item: WorkItem
		prop: string
		editable?: boolean
		/** Icon-only rendering for dense rows. */
		compact?: boolean
		bordered?: boolean
	}>(),
	{ editable: true, compact: false, bordered: false },
)
const emit = defineEmits<{ update: [values: Partial<WorkItem>] }>()

const opts = useProjectOptions(toRef(() => props.item.project))

// A completed cycle the item already sits in still needs a label.
const cycleOptions = computed(() => {
	const list = opts.cycles.value
	const current = props.item.cycle
	if (current && !list.some((c) => c.value === current)) {
		const c = opts.cycleOf(current)
		if (c) return [...list, { value: c.name, label: c.title, icon: 'lucide-refresh-ccw' }]
	}
	return list
})

// Items still in intake triage show their (otherwise hidden) Triage state.
const stateOptions = computed(() => {
	const list = opts.states.value
	if (props.item.state_group !== 'Triage') return list
	const s = opts.stateOf(props.item.state)
	return s
		? [{ value: s.name, label: s.title, stateGroup: s.state_group, color: s.color }, ...list]
		: list
})

function set(values: Partial<WorkItem>) {
	emit('update', values)
}
</script>
