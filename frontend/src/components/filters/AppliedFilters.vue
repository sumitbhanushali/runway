<template>
	<div
		v-if="chips.length"
		class="flex flex-wrap items-center gap-1.5 border-b border-outline-gray-1 px-4 py-2"
	>
		<span
			v-for="chip in chips"
			:key="chip.key + chip.value"
			class="flex items-center gap-1 rounded-3 border border-outline-gray-2 bg-surface-gray-1 py-0.5 pl-2 pr-1 text-xs text-ink-gray-7"
		>
			<span class="text-ink-gray-5">{{ chip.label }}:</span> {{ chip.text }}
			<button
				type="button"
				class="rounded-1 p-0.5 hover:bg-surface-gray-3"
				@click="remove(chip.key, chip.value)"
			>
				<span class="lucide-x block size-3" />
			</button>
		</span>
		<button
			type="button"
			class="text-xs text-ink-gray-5 hover:text-ink-gray-8"
			@click="filters = { search: filters.search }"
		>
			Clear all
		</button>
	</div>
</template>

<script setup lang="ts">
import { computed, toRef } from 'vue'
import { useProjectOptions } from '@/composables/useProjectOptions'
import { useWorkspace } from '@/stores/workspace'
import type { Filters } from '@/types'

const props = defineProps<{ project?: string | null }>()
const filters = defineModel<Filters>({ required: true })

const ws = useWorkspace()
const opts = useProjectOptions(toRef(() => props.project))

const LABELS: Record<string, string> = {
	state: 'State',
	state_group: 'Group',
	priority: 'Priority',
	assignees: 'Assignee',
	labels: 'Label',
	cycle: 'Cycle',
	modules: 'Module',
	owner: 'Created by',
	due: 'Due',
}

function text(key: string, value: string | null): string {
	if (key === 'state') return opts.stateOf(value)?.title ?? String(value)
	if (key === 'assignees' || key === 'owner') return ws.userName(value)
	if (key === 'labels') return opts.labelOf(value ?? '')?.title ?? String(value)
	if (key === 'cycle') return value ? (opts.cycleOf(value)?.title ?? value) : 'No cycle'
	if (key === 'modules') return opts.moduleOf(value ?? '')?.title ?? String(value)
	return String(value)
}

const chips = computed(() => {
	const out: { key: string; value: string | null; label: string; text: string }[] = []
	for (const [key, raw] of Object.entries(filters.value)) {
		if (key === 'search' || !raw) continue
		const values = Array.isArray(raw) ? raw : [raw]
		for (const v of values)
			out.push({
				key,
				value: v as string | null,
				label: LABELS[key] ?? key,
				text: text(key, v as string | null),
			})
	}
	return out
})

function remove(key: string, value: string | null) {
	const next = { ...filters.value } as Record<string, unknown>
	const cur = next[key]
	if (Array.isArray(cur)) next[key] = cur.filter((v) => v !== value)
	else delete next[key]
	filters.value = next as Filters
}
</script>
