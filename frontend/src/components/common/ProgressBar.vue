<template>
	<div class="flex items-center gap-2">
		<div class="flex h-1.5 flex-1 overflow-hidden rounded-full bg-surface-gray-3">
			<div
				v-for="seg in segments"
				:key="seg.group"
				class="h-full"
				:style="{ width: `${seg.pct}%`, background: STATE_GROUP_COLORS[seg.group] }"
			/>
		</div>
		<span class="w-10 text-right text-xs text-ink-gray-6">{{ progress.percent }}%</span>
	</div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Progress, StateGroup } from '@/types'
import { STATE_GROUP_COLORS } from '@/utils/constants'

const props = defineProps<{ progress: Progress }>()
const ORDER: StateGroup[] = ['Completed', 'Started', 'Unstarted', 'Backlog']
const segments = computed(() => {
	const total = props.progress.total || 1
	return ORDER.map((g) => ({
		group: g,
		pct: ((props.progress.by_group[g] ?? 0) / total) * 100,
	})).filter((s) => s.pct)
})
</script>
