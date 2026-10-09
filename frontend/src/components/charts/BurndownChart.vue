<template>
	<div class="h-64">
		<LineChart
			title="Burndown"
			:subtitle="by === 'points' ? 'Estimate points remaining' : 'Work items remaining'"
			:data="rows"
			x="day"
			:y="['Ideal', 'Remaining']"
			:x-axis="{ type: 'time' }"
			:y-axis="{ min: 0 }"
			:loading="loading"
		>
			<template #actions>
				<TabButtons
					v-model="by"
					size="sm"
					:options="[
						{ value: 'count', label: 'Items' },
						{ value: 'points', label: 'Points' },
					]"
				/>
			</template>
		</LineChart>
	</div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { TabButtons } from 'frappe-ui'
import { LineChart } from 'frappe-ui/charts'
import { api } from '@/api'

const props = defineProps<{ cycle: string; version?: number }>()
const by = ref<'count' | 'points'>('count')
const data = ref<Awaited<ReturnType<typeof api.burndown>> | null>(null)
const loading = ref(false)

watch(
	[() => props.cycle, by, () => props.version],
	async () => {
		loading.value = true
		try {
			data.value = await api.burndown(props.cycle, by.value)
		} finally {
			loading.value = false
		}
	},
	{ immediate: true },
)

const rows = computed(() =>
	(data.value?.days ?? []).map((day, i) => ({
		day,
		Ideal: data.value!.ideal[i],
		Remaining: data.value!.actual[i],
	})),
)
</script>
