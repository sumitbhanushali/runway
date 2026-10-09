<template>
	<AppHeader :crumbs="crumbs">
		<template #after-title>
			<button
				type="button"
				class="ml-1 rounded-3 p-1 hover:bg-surface-gray-2"
				@click="ws.toggleFavorite('Runway Project', project)"
			>
				<span
					class="block size-4"
					:class="
						ws.isFavorite('Runway Project', project)
							? 'lucide-star text-ink-amber-3'
							: 'lucide-star text-ink-gray-4'
					"
				/>
			</button>
		</template>
		<template #actions>
			<ProjectTabs :project="project" />
		</template>
	</AppHeader>
	<WorkItemsBoard v-if="projectDoc" ref="board" :state="display" :project="project">
		<template #toolbar>
			<Button
				v-if="projectDoc.views_enabled"
				size="sm"
				icon-left="lucide-save"
				label="Save view"
				@click="saveOpen = true"
			/>
		</template>
	</WorkItemsBoard>
	<EmptyState
		v-else
		icon="lucide-lock"
		title="Project not found"
		description="It may be secret, archived, or you are not a member."
	/>
	<SaveViewDialog v-model:open="saveOpen" :project="project" :state="display" />
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { Button } from 'frappe-ui'
import AppHeader from '@/components/common/AppHeader.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ProjectTabs from '@/components/common/ProjectTabs.vue'
import SaveViewDialog from '@/components/filters/SaveViewDialog.vue'
import WorkItemsBoard from '@/components/workitem/WorkItemsBoard.vue'
import { useDisplay } from '@/composables/useDisplay'
import { useWorkspace } from '@/stores/workspace'

const props = defineProps<{ project: string }>()
const ws = useWorkspace()
const projectDoc = computed(() => ws.project(props.project))
const display = useDisplay(`project:${props.project}`)
const saveOpen = ref(false)

const crumbs = computed(() => [
	{
		label: projectDoc.value?.title ?? props.project,
		route: { name: 'ProjectItems', params: { project: props.project } },
	},
	{ label: 'Work items' },
])
</script>
