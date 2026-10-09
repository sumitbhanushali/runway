<template>
	<AppHeader :crumbs="[{ label: 'Analytics', icon: 'lucide-chart-column' }]">
		<template #actions>
			<Button
				size="sm"
				icon-left="lucide-download"
				label="Export CSV"
				:loading="exporting"
				@click="exportCsv"
			/>
		</template>
	</AppHeader>
	<div class="flex-1 overflow-y-auto">
		<div class="mx-auto max-w-6xl space-y-5 p-6">
			<div class="flex flex-wrap items-end gap-3">
				<div class="w-56">
					<FormControl
						v-model="project"
						type="select"
						label="Scope"
						:options="scopeOptions"
					/>
				</div>
				<div class="w-44">
					<FormControl v-model="xAxis" type="select" label="X-axis" :options="AXES" />
				</div>
				<div class="w-40">
					<FormControl v-model="yAxis" type="select" label="Y-axis" :options="Y_AXES" />
				</div>
				<div class="w-44">
					<FormControl
						v-model="segment"
						type="select"
						label="Segment by"
						:options="[
							{ label: 'None', value: '' },
							...AXES.filter((a) => a.value !== xAxis),
						]"
					/>
				</div>
			</div>

			<div v-if="data" class="grid grid-cols-2 gap-3 sm:grid-cols-5">
				<div
					v-for="(count, group) in data.summary"
					:key="group"
					class="rounded-5 border border-outline-gray-1 p-3"
				>
					<div class="flex items-center gap-1.5 text-sm text-ink-gray-5">
						<StateIcon :group="group as StateGroup" :size="12" /> {{ group }}
					</div>
					<div class="mt-1 text-xl font-semibold text-ink-gray-9">{{ count }}</div>
				</div>
			</div>

			<div class="h-96 rounded-5 border border-outline-gray-1 p-4">
				<BarChart
					:title="`${Y_AXES.find((y) => y.value === yAxis)?.label} by ${AXES.find((a) => a.value === xAxis)?.label.toLowerCase()}`"
					:data="chartRows"
					x="label"
					:y="seriesKeys"
					:stacked="!!segment"
					:loading="loading"
				/>
			</div>

			<div
				v-if="data?.rows.length"
				class="overflow-hidden rounded-5 border border-outline-gray-1"
			>
				<table class="w-full text-sm">
					<thead class="bg-surface-gray-1 text-left text-ink-gray-6">
						<tr>
							<th class="px-4 py-2 font-medium">
								{{ AXES.find((a) => a.value === xAxis)?.label }}
							</th>
							<th
								v-for="s in data.segments"
								:key="s.key"
								class="px-4 py-2 font-medium"
							>
								{{ s.label }}
							</th>
							<th class="px-4 py-2 text-right font-medium">Total</th>
						</tr>
					</thead>
					<tbody>
						<tr
							v-for="r in data.rows"
							:key="String(r.key)"
							class="border-t border-outline-gray-1"
						>
							<td class="px-4 py-2 text-ink-gray-8">{{ r.label }}</td>
							<td
								v-for="s in data.segments"
								:key="s.key"
								class="px-4 py-2 text-ink-gray-6"
							>
								{{ r.segments[s.key] ?? 0 }}
							</td>
							<td class="px-4 py-2 text-right font-medium text-ink-gray-9">
								{{ r.value }}
							</td>
						</tr>
					</tbody>
				</table>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { Button, FormControl, toast } from 'frappe-ui'
import { BarChart } from 'frappe-ui/charts'
import AppHeader from '@/components/common/AppHeader.vue'
import StateIcon from '@/components/common/StateIcon.vue'
import { api, errorMessage } from '@/api'
import { useWorkspace } from '@/stores/workspace'
import type { StateGroup } from '@/types'

const AXES = [
	{ label: 'State group', value: 'state_group' },
	{ label: 'State', value: 'state' },
	{ label: 'Priority', value: 'priority' },
	{ label: 'Assignee', value: 'assignees' },
	{ label: 'Label', value: 'labels' },
	{ label: 'Cycle', value: 'cycle' },
	{ label: 'Module', value: 'modules' },
	{ label: 'Created by', value: 'owner' },
	{ label: 'Due month', value: 'due_month' },
]
const Y_AXES = [
	{ label: 'Work items', value: 'count' },
	{ label: 'Estimate points', value: 'points' },
]

const ws = useWorkspace()
const project = ref('')
const xAxis = ref('state_group')
const yAxis = ref('count')
const segment = ref('')
const data = ref<Awaited<ReturnType<typeof api.analytics>> | null>(null)
const loading = ref(false)
const exporting = ref(false)

const scopeOptions = computed(() => [
	{ label: 'All projects', value: '' },
	...ws.projects.value.map((p) => ({ label: p.title, value: p.name })),
])

async function load() {
	loading.value = true
	try {
		data.value = await api.analytics({
			workspace: project.value ? null : ws.workspace.value,
			project: project.value || null,
			x_axis: xAxis.value,
			y_axis: yAxis.value,
			segment: segment.value || null,
		})
	} catch (e) {
		toast.error(errorMessage(e))
	} finally {
		loading.value = false
	}
}
watch([project, xAxis, yAxis, segment], load, { immediate: true })
watch(xAxis, (x) => {
	if (segment.value === x) segment.value = ''
})

const seriesKeys = computed(() =>
	segment.value && data.value?.segments.length
		? data.value.segments.map((s) => s.label)
		: ['value'],
)
const chartRows = computed(() =>
	(data.value?.rows ?? []).map((r) => {
		const row: Record<string, string | number> = { label: r.label, value: r.value }
		for (const s of data.value?.segments ?? []) row[s.label] = r.segments[s.key] ?? 0
		return row
	}),
)

async function exportCsv() {
	exporting.value = true
	try {
		const csv = await api.exportCsv({
			workspace: project.value ? null : ws.workspace.value,
			project: project.value || null,
		})
		const blob = new Blob([csv], { type: 'text/csv' })
		const a = document.createElement('a')
		a.href = URL.createObjectURL(blob)
		a.download = `runway-${project.value || ws.workspace.value}-work-items.csv`
		a.click()
		URL.revokeObjectURL(a.href)
	} catch (e) {
		toast.error(errorMessage(e))
	} finally {
		exporting.value = false
	}
}
</script>
