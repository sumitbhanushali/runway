<template>
	<nav v-if="p" class="flex items-center gap-0.5 rounded-4 bg-surface-gray-2 p-0.5">
		<router-link
			v-for="t in tabs"
			:key="t.name"
			v-slot="{ href, navigate, isActive }"
			:to="{ name: t.name, params: { project } }"
			custom
		>
			<a
				:href="href"
				class="flex h-6 items-center gap-1.5 rounded-3 px-2 text-sm"
				:class="
					isActive || activeName === t.name || t.also?.includes(activeName)
						? 'bg-surface-base text-ink-gray-9 shadow-sm'
						: 'text-ink-gray-6 hover:text-ink-gray-8'
				"
				@click="navigate"
			>
				<span :class="t.icon" class="size-3.5" />
				<span class="hidden lg:inline">{{ t.label }}</span>
			</a>
		</router-link>
	</nav>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useWorkspace } from '@/stores/workspace'

const props = defineProps<{ project: string }>()
const ws = useWorkspace()
const route = useRoute()
const p = computed(() => ws.project(props.project))
const activeName = computed(() => String(route.name))

const tabs = computed(() => {
	const x = p.value
	if (!x) return []
	return [
		{ name: 'ProjectItems', label: 'Work items', icon: 'lucide-layers-2' },
		x.cycles_enabled && {
			name: 'Cycles',
			label: 'Cycles',
			icon: 'lucide-refresh-ccw',
			also: ['Cycle'],
		},
		x.modules_enabled && {
			name: 'Modules',
			label: 'Modules',
			icon: 'lucide-boxes',
			also: ['Module'],
		},
		x.views_enabled && {
			name: 'ProjectViews',
			label: 'Views',
			icon: 'lucide-layers',
			also: ['ProjectView'],
		},
		x.intake_enabled && { name: 'Intake', label: 'Intake', icon: 'lucide-inbox' },
		x.role === 'Admin' && {
			name: 'ProjectSettings',
			label: 'Settings',
			icon: 'lucide-settings',
		},
	].filter(Boolean) as { name: string; label: string; icon: string; also?: string[] }[]
})
</script>
