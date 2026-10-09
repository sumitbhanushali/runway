<template>
	<AppHeader
		:crumbs="[
			{
				label: projectDoc?.title ?? project,
				route: { name: 'ProjectItems', params: { project } },
			},
			{ label: 'Cycles', route: { name: 'Cycles', params: { project } } },
			{ label: cycleDoc?.title ?? '…' },
		]"
	>
		<template #after-title>
			<Badge
				v-if="cycleDoc"
				class="ml-2"
				size="sm"
				:label="cycleDoc.status"
				:theme="cycleDoc.status === 'Current' ? 'green' : 'gray'"
			/>
		</template>
		<template #actions>
			<Button
				size="sm"
				:icon-left="showStats ? 'lucide-panel-right-close' : 'lucide-panel-right-open'"
				label="Progress"
				@click="showStats = !showStats"
			/>
			<Button
				v-if="cycleDoc && !cycleDoc.completed_at && canEdit"
				size="sm"
				variant="solid"
				icon-left="lucide-circle-check"
				label="Complete cycle"
				@click="completeOpen = true"
			/>
		</template>
	</AppHeader>
	<div class="flex min-h-0 flex-1">
		<WorkItemsBoard
			ref="board"
			:state="display"
			:project="project"
			:cycle="cycle"
			:defaults="cycleDoc?.completed_at ? {} : { cycle }"
			:hide-filters="['cycle']"
			empty-title="No work items in this cycle"
			empty-description="Add work items here, or set the cycle on existing items."
		/>
		<aside
			v-if="showStats && cycleDoc"
			class="w-96 shrink-0 space-y-5 overflow-y-auto border-l border-outline-gray-1 p-4"
		>
			<div class="space-y-1 text-sm">
				<div class="text-ink-gray-5">
					{{
						cycleDoc.start_date
							? `${dayjs(cycleDoc.start_date).format('MMM D')} – ${dayjs(cycleDoc.end_date).format('MMM D, YYYY')}`
							: 'No dates set'
					}}
				</div>
				<p v-if="cycleDoc.description" class="text-ink-gray-7">
					{{ cycleDoc.description }}
				</p>
			</div>
			<ProgressBar :progress="cycleDoc.progress" />
			<div class="grid grid-cols-2 gap-2">
				<div
					v-for="(n, g) in cycleDoc.progress.by_group"
					v-show="g !== 'Triage'"
					:key="g"
					class="flex items-center gap-2 text-sm"
				>
					<StateIcon :group="g as StateGroup" />
					<span class="flex-1 text-ink-gray-6">{{ g }}</span>
					<span class="text-ink-gray-9">{{ n }}</span>
				</div>
			</div>
			<BurndownChart :cycle="cycle" :version="version" />
			<div
				v-if="cycleDoc.completed_at"
				class="rounded-4 bg-surface-gray-1 p-3 text-sm text-ink-gray-6"
			>
				Completed {{ dayjs(cycleDoc.completed_at).format('MMM D, YYYY') }}. The progress
				shown is the snapshot frozen at completion.
			</div>
		</aside>
	</div>

	<Dialog v-model:open="completeOpen" title="Complete cycle" size="md">
		<template #default>
			<div class="space-y-3 text-sm text-ink-gray-7">
				<p>
					{{ pending }} unfinished work item{{ pending === 1 ? '' : 's' }} in this cycle.
					Progress will be frozen as a snapshot.
				</p>
				<FormControl
					v-model="transferTo"
					type="select"
					label="Move unfinished items to"
					:options="[{ label: 'Leave them in this cycle', value: '' }, ...openCycles]"
				/>
			</div>
		</template>
		<template #actions>
			<div class="flex justify-end gap-2">
				<Button label="Cancel" @click="completeOpen = false" />
				<Button variant="solid" label="Complete" :loading="completing" @click="complete" />
			</div>
		</template>
	</Dialog>
</template>

<script setup lang="ts">
import { computed, onMounted, onScopeDispose, ref } from 'vue'
import { Badge, Button, Dialog, FormControl, dayjs, toast } from 'frappe-ui'
import BurndownChart from '@/components/charts/BurndownChart.vue'
import AppHeader from '@/components/common/AppHeader.vue'
import ProgressBar from '@/components/common/ProgressBar.vue'
import StateIcon from '@/components/common/StateIcon.vue'
import WorkItemsBoard from '@/components/workitem/WorkItemsBoard.vue'
import { api, errorMessage } from '@/api'
import { useDisplay } from '@/composables/useDisplay'
import { refreshProject, useWorkspace } from '@/stores/workspace'
import type { Cycle, StateGroup } from '@/types'
import { bus } from '@/utils/bus'

const props = defineProps<{ project: string; cycle: string }>()
const ws = useWorkspace()
const projectDoc = computed(() => ws.project(props.project))
const canEdit = computed(() => projectDoc.value?.role !== 'Guest')
const display = useDisplay(`cycle:${props.cycle}`, {
	display: {
		layout: 'kanban',
		group_by: 'state',
		order_by: 'sort_order',
		show_sub_items: true,
		show_empty_groups: true,
	},
})
const cycles = ref<Cycle[]>([])
const cycleDoc = computed(() => cycles.value.find((c) => c.name === props.cycle))
const showStats = ref(true)
const completeOpen = ref(false)
const completing = ref(false)
const transferTo = ref('')
const version = ref(0)
const board = ref<{ reload: () => void } | null>(null)

async function load() {
	cycles.value = await api.cycles(props.project)
	version.value++
}
onMounted(load)
onScopeDispose(bus.on('item-updated', load))

const pending = computed(() => {
	const p = cycleDoc.value?.progress.by_group
	return p ? (p.Backlog ?? 0) + (p.Unstarted ?? 0) + (p.Started ?? 0) : 0
})
const openCycles = computed(() =>
	cycles.value
		.filter((c) => c.name !== props.cycle && !c.completed_at)
		.map((c) => ({ label: c.title, value: c.name })),
)

async function complete() {
	completing.value = true
	try {
		const res = await api.completeCycle(props.cycle, transferTo.value || null)
		toast.success(
			res.transferred
				? `Cycle completed · ${res.transferred} items moved`
				: 'Cycle completed',
		)
		completeOpen.value = false
		await Promise.all([load(), refreshProject(props.project)])
		board.value?.reload()
	} catch (e) {
		toast.error(errorMessage(e))
	} finally {
		completing.value = false
	}
}
</script>
