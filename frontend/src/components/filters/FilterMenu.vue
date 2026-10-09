<template>
	<Popover align="end" :offset="4" bare>
		<template #trigger>
			<Button
				size="sm"
				icon-left="lucide-list-filter"
				:label="count ? `Filters · ${count}` : 'Filters'"
			/>
		</template>
		<template #default>
			<div class="w-72 rounded-4 bg-surface-elevation-2 p-1 shadow-2xl ring-1 ring-black/5">
				<input
					v-model="query"
					class="mb-1 h-7 w-full rounded-3 border-0 bg-surface-gray-2 px-2 text-sm placeholder-ink-gray-4 focus:ring-0"
					placeholder="Search filters…"
				/>
				<div class="max-h-96 overflow-y-auto">
					<div v-for="section in visibleSections" :key="section.key" class="mb-1">
						<button
							type="button"
							class="flex w-full items-center gap-1.5 rounded-3 px-2 py-1 text-xs font-medium uppercase tracking-wide text-ink-gray-5 hover:bg-surface-gray-2"
							@click="openSection[section.key] = !isOpen(section.key)"
						>
							<span
								:class="
									isOpen(section.key)
										? 'lucide-chevron-down'
										: 'lucide-chevron-right'
								"
								class="size-3"
							/>
							{{ section.label }}
							<span
								v-if="selectedCount(section.key)"
								class="ml-auto normal-case text-ink-gray-7"
							>
								{{ selectedCount(section.key) }}
							</span>
						</button>
						<template v-if="isOpen(section.key)">
							<button
								v-for="opt in section.options"
								:key="String(opt.value)"
								type="button"
								class="flex w-full items-center gap-2 rounded-3 px-2 py-1.5 text-left text-sm text-ink-gray-8 hover:bg-surface-gray-2"
								@click="toggle(section.key, opt.value)"
							>
								<span
									class="flex size-3.5 shrink-0 items-center justify-center rounded-1 border"
									:class="
										has(section.key, opt.value)
											? 'border-outline-gray-7 bg-surface-gray-7'
											: 'border-outline-gray-3'
									"
								>
									<span
										v-if="has(section.key, opt.value)"
										class="lucide-check size-3 text-ink-base"
									/>
								</span>
								<OptionMark :option="opt" />
								<span class="truncate">{{ opt.label }}</span>
							</button>
						</template>
					</div>
				</div>
				<button
					v-if="count"
					type="button"
					class="mt-1 w-full rounded-3 border-t border-outline-gray-1 px-2 py-1.5 text-left text-sm text-ink-gray-5 hover:bg-surface-gray-2"
					@click="clearAll"
				>
					Clear all filters
				</button>
			</div>
		</template>
	</Popover>
</template>

<script setup lang="ts">
import { computed, reactive, ref, toRef } from 'vue'
import { Button, Popover } from 'frappe-ui'
import OptionMark from '@/components/pickers/OptionMark.vue'
import type { PickerOption } from '@/components/pickers/types'
import { activeFilterCount } from '@/composables/useDisplay'
import { useProjectOptions } from '@/composables/useProjectOptions'
import { useWorkspace } from '@/stores/workspace'
import type { Filters } from '@/types'
import { PRIORITIES, STATE_GROUPS, STATE_GROUP_COLORS } from '@/utils/constants'

const props = defineProps<{ project?: string | null; hide?: string[] }>()
const filters = defineModel<Filters>({ required: true })

const ws = useWorkspace()
const opts = useProjectOptions(toRef(() => props.project))
const query = ref('')
const openSection = reactive<Record<string, boolean>>({})

type Key = keyof Filters
interface Section {
	key: Key
	label: string
	options: PickerOption[]
}

const sections = computed<Section[]>(() => {
	const people: PickerOption[] = (opts.project.value?.members ?? ws.members.value).map((m) => ({
		value: m.user,
		label: m.full_name || m.user,
		user: m.user,
	}))
	const list: Section[] = []
	if (opts.project.value) list.push({ key: 'state', label: 'State', options: opts.states.value })
	else
		list.push({
			key: 'state_group',
			label: 'State group',
			options: STATE_GROUPS.map((g) => ({
				value: g,
				label: g,
				stateGroup: g,
				color: STATE_GROUP_COLORS[g],
			})),
		})
	list.push({
		key: 'priority',
		label: 'Priority',
		options: PRIORITIES.map((p) => ({ value: p, label: p, priority: p })),
	})
	list.push({ key: 'assignees', label: 'Assignees', options: people })
	if (opts.project.value) {
		list.push({ key: 'labels', label: 'Labels', options: opts.labels.value })
		if (opts.project.value.cycles_enabled)
			list.push({
				key: 'cycle',
				label: 'Cycle',
				options: [
					...opts.cycles.value,
					{ value: '', label: 'No cycle', icon: 'lucide-circle-dashed' },
				],
			})
		if (opts.project.value.modules_enabled)
			list.push({ key: 'modules', label: 'Modules', options: opts.modules.value })
	}
	list.push({ key: 'owner', label: 'Created by', options: people })
	list.push({
		key: 'due',
		label: 'Due',
		options: [{ value: 'overdue', label: 'Overdue', icon: 'lucide-alarm-clock' }],
	})
	return list.filter((s) => !props.hide?.includes(s.key))
})

const visibleSections = computed(() => {
	const q = query.value.trim().toLowerCase()
	if (!q) return sections.value
	return sections.value
		.map((s) => ({
			...s,
			options: s.label.toLowerCase().includes(q)
				? s.options
				: s.options.filter((o) => o.label.toLowerCase().includes(q)),
		}))
		.filter((s) => s.options.length)
})

const count = computed(() => activeFilterCount(filters.value))

function isOpen(key: string) {
	return openSection[key] ?? (!!query.value || selectedCount(key as Key) > 0)
}

function values(key: Key): string[] {
	const v = filters.value[key]
	if (key === 'due') return v ? [v as string] : []
	return ((v as (string | null)[] | undefined) ?? []).map((x) => x ?? '')
}

function selectedCount(key: Key) {
	return values(key).length
}

function has(key: Key, value: string) {
	return values(key).includes(value)
}

function toggle(key: Key, value: string) {
	const next = { ...filters.value }
	if (key === 'due') {
		next.due = next.due === value ? undefined : (value as 'overdue')
	} else {
		const cur = values(key)
		const list = cur.includes(value) ? cur.filter((v) => v !== value) : [...cur, value]
		;(next as Record<string, unknown>)[key] =
			key === 'cycle' ? list.map((v) => v || null) : list
	}
	filters.value = next
}

function clearAll() {
	filters.value = { search: filters.value.search }
}
</script>
