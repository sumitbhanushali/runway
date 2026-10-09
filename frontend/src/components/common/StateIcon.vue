<template>
	<svg :width="size" :height="size" viewBox="0 0 16 16" class="shrink-0" aria-hidden="true">
		<circle
			v-if="group === 'Backlog' || group === 'Triage'"
			cx="8"
			cy="8"
			r="6"
			fill="none"
			:stroke="color"
			stroke-width="1.6"
			stroke-dasharray="2.4 2"
		/>
		<circle v-else cx="8" cy="8" r="6" fill="none" :stroke="color" stroke-width="1.6" />
		<path v-if="group === 'Started'" d="M8 4 A4 4 0 0 1 8 12 Z" :fill="color" />
		<template v-if="group === 'Completed'">
			<circle cx="8" cy="8" r="6" :fill="color" />
			<path
				d="M5.4 8.2 7.2 10l3.4-3.6"
				fill="none"
				stroke="#fff"
				stroke-width="1.6"
				stroke-linecap="round"
			/>
		</template>
		<template v-if="group === 'Cancelled'">
			<circle cx="8" cy="8" r="6" :fill="color" />
			<path d="M6 6l4 4M10 6l-4 4" stroke="#fff" stroke-width="1.6" stroke-linecap="round" />
		</template>
	</svg>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { StateGroup } from '@/types'
import { STATE_GROUP_COLORS } from '@/utils/constants'

const props = withDefaults(
	defineProps<{ group: StateGroup; color?: string | null; size?: number }>(),
	{
		size: 14,
	},
)
const color = computed(() => props.color || STATE_GROUP_COLORS[props.group])
</script>
