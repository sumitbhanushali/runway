<template>
	<AppHeader
		:crumbs="[
			{
				label: projectDoc?.title ?? project,
				route: { name: 'ProjectItems', params: { project } },
			},
			{ label: 'Modules' },
		]"
	>
		<template #actions>
			<ProjectTabs :project="project" />
			<Button
				v-if="canEdit"
				variant="solid"
				icon-left="lucide-plus"
				label="New module"
				@click="edit(null)"
			/>
		</template>
	</AppHeader>
	<div class="flex-1 overflow-y-auto p-6">
		<EmptyState
			v-if="loaded && !modules.length"
			icon="lucide-boxes"
			title="No modules yet"
			description="Modules group work by feature or epic and can span several cycles."
		>
			<Button v-if="canEdit" variant="solid" label="Create module" @click="edit(null)" />
		</EmptyState>
		<div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
			<router-link
				v-for="m in modules"
				:key="m.name"
				:to="{ name: 'Module', params: { project, module: m.name } }"
				class="flex flex-col gap-3 rounded-5 border border-outline-gray-1 p-4 hover:border-outline-gray-3"
			>
				<div class="flex items-center gap-2">
					<span class="lucide-boxes size-4 text-ink-gray-5" />
					<span class="flex-1 truncate font-medium text-ink-gray-9">{{ m.title }}</span>
					<Badge size="sm" :label="m.status" :theme="STATUS_THEME[m.status] ?? 'gray'" />
				</div>
				<ProgressBar :progress="m.progress" />
				<div class="flex items-center justify-between text-xs text-ink-gray-5">
					<span>{{ m.progress.completed }}/{{ m.progress.total }} done</span>
					<span v-if="m.target_date"
						>Target {{ dayjs(m.target_date).format('MMM D, YYYY') }}</span
					>
					<UserAvatar v-if="m.lead" :user="m.lead" size="xs" />
				</div>
			</router-link>
		</div>
	</div>
	<ModuleDialog v-model:open="dialogOpen" :project="project" :module="editing" @saved="load" />
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { Badge, Button, dayjs } from 'frappe-ui'
import AppHeader from '@/components/common/AppHeader.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ModuleDialog from '@/components/common/ModuleDialog.vue'
import ProgressBar from '@/components/common/ProgressBar.vue'
import ProjectTabs from '@/components/common/ProjectTabs.vue'
import UserAvatar from '@/components/common/UserAvatar.vue'
import { api } from '@/api'
import { useWorkspace } from '@/stores/workspace'
import type { Module } from '@/types'
import { STATUS_THEME } from '@/utils/modules'

const props = defineProps<{ project: string }>()
const ws = useWorkspace()
const projectDoc = computed(() => ws.project(props.project))
const canEdit = computed(() => projectDoc.value?.role !== 'Guest')
const modules = ref<Module[]>([])
const loaded = ref(false)
const dialogOpen = ref(false)
const editing = ref<Module | null>(null)

async function load() {
	modules.value = await api.modules(props.project)
	loaded.value = true
}
onMounted(load)

function edit(m: Module | null) {
	editing.value = m
	dialogOpen.value = true
}
</script>
