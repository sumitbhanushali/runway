<template>
	<AppHeader :crumbs="crumbs">
		<template v-if="project" #actions><ProjectTabs :project="project" /></template>
	</AppHeader>
	<div class="flex-1 overflow-y-auto p-6">
		<div class="mx-auto max-w-4xl space-y-6">
			<section v-if="!project">
				<h2 class="mb-2 text-sm font-medium text-ink-gray-6">Built-in</h2>
				<div class="grid gap-2 sm:grid-cols-2">
					<router-link
						v-for="b in BUILT_IN"
						:key="b.name"
						:to="{ name: 'WorkspaceView', params: { view: b.name } }"
						class="flex items-center gap-3 rounded-4 border border-outline-gray-1 px-4 py-3 hover:bg-surface-gray-1"
					>
						<span :class="b.icon" class="size-4 text-ink-gray-5" />
						<span class="text-sm font-medium text-ink-gray-8">{{ b.title }}</span>
					</router-link>
				</div>
			</section>
			<section>
				<h2 class="mb-2 text-sm font-medium text-ink-gray-6">Saved views</h2>
				<div
					v-if="views.length"
					class="overflow-hidden rounded-5 border border-outline-gray-1"
				>
					<div
						v-for="v in views"
						:key="v.name"
						class="flex items-center gap-3 border-b border-outline-gray-1 px-4 py-3 last:border-b-0 hover:bg-surface-gray-1"
					>
						<span class="lucide-layers size-4 text-ink-gray-5" />
						<router-link :to="viewRoute(v)" class="min-w-0 flex-1">
							<div class="truncate text-sm font-medium text-ink-gray-8">
								{{ v.title }}
							</div>
							<div v-if="v.description" class="truncate text-xs text-ink-gray-5">
								{{ v.description }}
							</div>
						</router-link>
						<Badge
							size="sm"
							:label="v.access"
							:theme="v.access === 'Public' ? 'blue' : 'gray'"
						/>
						<UserAvatar :user="v.owner" size="xs" />
						<Button
							v-if="v.owner === ws.user.value?.name"
							size="sm"
							variant="ghost"
							icon="lucide-trash-2"
							@click="remove(v)"
						/>
					</div>
				</div>
				<EmptyState
					v-else
					icon="lucide-layers"
					title="No saved views"
					description="Filter a work item list, then use “Save view” to keep it here."
				/>
			</section>
		</div>
	</div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { Badge, Button, dialog } from 'frappe-ui'
import AppHeader from '@/components/common/AppHeader.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ProjectTabs from '@/components/common/ProjectTabs.vue'
import UserAvatar from '@/components/common/UserAvatar.vue'
import { api } from '@/api'
import { useWorkspace } from '@/stores/workspace'
import type { SavedView } from '@/types'
import { BUILT_IN } from '@/utils/views'

const props = defineProps<{ project?: string }>()
const ws = useWorkspace()
const views = ref<SavedView[]>([])

const crumbs = computed(() =>
	props.project
		? [
				{
					label: ws.project(props.project)?.title ?? props.project,
					route: { name: 'ProjectItems', params: { project: props.project } },
				},
				{ label: 'Views' },
			]
		: [{ label: 'Views', icon: 'lucide-layers' }],
)

async function load() {
	views.value = await api.getList<SavedView>('Runway View', {
		fields: ['name', 'title', 'description', 'access', 'owner', 'project', 'workspace'],
		filters: props.project
			? { project: props.project }
			: { workspace: ws.workspace.value, project: ['is', 'not set'] },
		order_by: 'modified desc',
		limit_page_length: 200,
	})
}
onMounted(load)

function viewRoute(v: SavedView) {
	return v.project
		? { name: 'ProjectView', params: { project: v.project, view: v.name } }
		: { name: 'WorkspaceView', params: { view: v.name } }
}

function remove(v: SavedView) {
	dialog.danger({
		title: `Delete “${v.title}”?`,
		onConfirm: async ({ close }) => {
			await api.remove('Runway View', v.name)
			close()
			load()
		},
	})
}
</script>
