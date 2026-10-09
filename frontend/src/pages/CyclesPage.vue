<template>
	<AppHeader
		:crumbs="[
			{
				label: projectDoc?.title ?? project,
				route: { name: 'ProjectItems', params: { project } },
			},
			{ label: 'Cycles' },
		]"
	>
		<template #actions>
			<ProjectTabs :project="project" />
			<Button
				v-if="canEdit"
				variant="solid"
				icon-left="lucide-plus"
				label="New cycle"
				@click="edit(null)"
			/>
		</template>
	</AppHeader>
	<div class="flex-1 overflow-y-auto">
		<EmptyState
			v-if="loaded && !cycles.length"
			icon="lucide-refresh-ccw"
			title="Plan your first cycle"
			description="Cycles are time-boxed iterations. Group work into them and track progress with a burndown."
		>
			<Button v-if="canEdit" variant="solid" label="Create cycle" @click="edit(null)" />
		</EmptyState>
		<section v-for="group in groups" :key="group.status">
			<div
				class="sticky top-0 border-b border-outline-gray-1 bg-surface-gray-1 px-6 py-2 text-sm font-medium text-ink-gray-7"
			>
				{{ group.status }} <span class="text-ink-gray-5">{{ group.cycles.length }}</span>
			</div>
			<router-link
				v-for="c in group.cycles"
				:key="c.name"
				:to="{ name: 'Cycle', params: { project, cycle: c.name } }"
				class="group flex items-center gap-4 border-b border-outline-gray-1 px-6 py-3 hover:bg-surface-gray-1"
			>
				<span class="lucide-refresh-ccw size-4 text-ink-gray-5" />
				<div class="min-w-0 flex-1">
					<div class="truncate text-sm font-medium text-ink-gray-9">{{ c.title }}</div>
					<div class="text-xs text-ink-gray-5">
						{{
							c.start_date
								? `${dayjs(c.start_date).format('MMM D')} – ${dayjs(c.end_date).format('MMM D, YYYY')}`
								: 'No dates'
						}}
						<template v-if="c.status === 'Current'">
							· {{ daysLeft(c.end_date) }}</template
						>
					</div>
				</div>
				<div class="w-56"><ProgressBar :progress="c.progress" /></div>
				<span class="w-20 text-right text-xs text-ink-gray-5"
					>{{ c.progress.completed }}/{{ c.progress.total }} done</span
				>
				<Dropdown v-if="canEdit" :options="menu(c)" @click.prevent>
					<template #default>
						<Button size="sm" variant="ghost" icon="lucide-ellipsis" @click.prevent />
					</template>
				</Dropdown>
			</router-link>
		</section>
	</div>
	<CycleDialog v-model:open="dialogOpen" :project="project" :cycle="editing" @saved="load" />
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { Button, Dropdown, dayjs, dialog, toast } from 'frappe-ui'
import AppHeader from '@/components/common/AppHeader.vue'
import CycleDialog from '@/components/common/CycleDialog.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ProgressBar from '@/components/common/ProgressBar.vue'
import ProjectTabs from '@/components/common/ProjectTabs.vue'
import { api, errorMessage } from '@/api'
import { refreshProject, useWorkspace } from '@/stores/workspace'
import type { Cycle } from '@/types'

const props = defineProps<{ project: string }>()
const ws = useWorkspace()
const projectDoc = computed(() => ws.project(props.project))
const canEdit = computed(() => projectDoc.value?.role !== 'Guest')
const cycles = ref<Cycle[]>([])
const loaded = ref(false)
const dialogOpen = ref(false)
const editing = ref<Cycle | null>(null)

async function load() {
	cycles.value = await api.cycles(props.project)
	loaded.value = true
}
onMounted(load)

const groups = computed(() =>
	(['Current', 'Upcoming', 'Draft', 'Completed'] as const)
		.map((status) => ({ status, cycles: cycles.value.filter((c) => c.status === status) }))
		.filter((g) => g.cycles.length),
)

function daysLeft(end: string | null) {
	const d = dayjs(end).diff(dayjs().startOf('day'), 'day')
	return d === 0 ? 'ends today' : `${d} day${d === 1 ? '' : 's'} left`
}

function edit(c: Cycle | null) {
	editing.value = c
	dialogOpen.value = true
}

function menu(c: Cycle) {
	return [
		{ label: 'Edit', icon: 'lucide-pencil', onClick: () => edit(c) },
		{
			label: 'Delete',
			icon: 'lucide-trash-2',
			theme: 'red' as const,
			onClick: () =>
				dialog.danger({
					title: `Delete ${c.title}?`,
					message: 'Work items in this cycle are kept and moved out of it.',
					onConfirm: async ({ close }) => {
						try {
							await api.remove('Runway Cycle', c.name)
							await refreshProject(props.project)
							close()
							load()
						} catch (e) {
							toast.error(errorMessage(e))
						}
					},
				}),
		},
	]
}
</script>
