<template>
	<AppHeader :crumbs="crumbs">
		<template v-if="project" #actions><ProjectTabs :project="project" /></template>
	</AppHeader>
	<ViewBoard v-if="builtIn" :key="view" :storage-key="`view:${view}`" :my-work="builtIn.myWork" />
	<ViewBoard
		v-else-if="doc"
		:key="doc.name + (doc as any).modified"
		:storage-key="`view:${doc.name}`"
		:doc="doc"
		:project="project"
		@saved="(d) => (doc = d)"
	/>
	<div v-else-if="!missing" class="p-6 text-sm text-ink-gray-5">Loading view…</div>
	<EmptyState
		v-else
		icon="lucide-eye-off"
		title="View not found"
		description="It may have been deleted or made private."
	/>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import AppHeader from '@/components/common/AppHeader.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ProjectTabs from '@/components/common/ProjectTabs.vue'
import ViewBoard from '@/components/workitem/ViewBoard.vue'
import { api } from '@/api'
import { useWorkspace } from '@/stores/workspace'
import type { SavedView } from '@/types'
import { BUILT_IN } from '@/utils/views'

const props = defineProps<{ view: string; project?: string }>()
const ws = useWorkspace()
const doc = ref<SavedView | null>(null)
const missing = ref(false)

const builtIn = computed(() =>
	props.project ? undefined : BUILT_IN.find((b) => b.name === props.view),
)

onMounted(async () => {
	if (builtIn.value) return
	try {
		doc.value = await api.getDoc<SavedView>('Runway View', props.view)
		api.recordVisit('Runway View', props.view).catch(() => {})
	} catch {
		missing.value = true
	}
})

const crumbs = computed(() => {
	const title = builtIn.value?.title ?? doc.value?.title ?? props.view
	return props.project
		? [
				{
					label: ws.project(props.project)?.title ?? props.project,
					route: { name: 'ProjectItems', params: { project: props.project } },
				},
				{
					label: 'Views',
					route: { name: 'ProjectViews', params: { project: props.project } },
				},
				{ label: title },
			]
		: [
				{ label: 'Views', icon: 'lucide-layers', route: { name: 'WorkspaceViews' } },
				{ label: title },
			]
})
</script>
