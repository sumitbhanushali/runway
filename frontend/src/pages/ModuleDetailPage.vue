<template>
	<AppHeader
		:crumbs="[
			{
				label: projectDoc?.title ?? project,
				route: { name: 'ProjectItems', params: { project } },
			},
			{ label: 'Modules', route: { name: 'Modules', params: { project } } },
			{ label: moduleDoc?.title ?? '…' },
		]"
	>
		<template #after-title>
			<Badge
				v-if="moduleDoc"
				class="ml-2"
				size="sm"
				:label="moduleDoc.status"
				:theme="STATUS_THEME[moduleDoc.status] ?? 'gray'"
			/>
		</template>
		<template #actions>
			<Button
				size="sm"
				:icon-left="showStats ? 'lucide-panel-right-close' : 'lucide-panel-right-open'"
				label="Details"
				@click="showStats = !showStats"
			/>
			<Button
				v-if="canEdit"
				size="sm"
				icon-left="lucide-pencil"
				label="Edit"
				@click="dialogOpen = true"
			/>
		</template>
	</AppHeader>
	<div class="flex min-h-0 flex-1">
		<WorkItemsBoard
			:state="display"
			:project="project"
			:module="module"
			:defaults="{ modules: [module] }"
			:hide-filters="['modules']"
			empty-title="No work items in this module"
		/>
		<aside
			v-if="showStats && moduleDoc"
			class="w-80 shrink-0 space-y-4 overflow-y-auto border-l border-outline-gray-1 p-4 text-sm"
		>
			<!-- eslint-disable-next-line vue/no-v-html -- Text Editor fields are sanitized by Frappe on save -->
			<div v-if="moduleDoc.description" class="runway-prose" v-html="moduleDoc.description" />
			<ProgressBar :progress="moduleDoc.progress" />
			<div class="grid grid-cols-[90px_1fr] gap-y-2">
				<span class="text-ink-gray-5">Lead</span>
				<span class="flex items-center gap-1.5 text-ink-gray-8">
					<template v-if="moduleDoc.lead"
						><UserAvatar :user="moduleDoc.lead" size="xs" />{{
							ws.userName(moduleDoc.lead)
						}}</template
					>
					<template v-else>—</template>
				</span>
				<span class="text-ink-gray-5">Start</span>
				<span class="text-ink-gray-8">{{
					moduleDoc.start_date ? dayjs(moduleDoc.start_date).format('MMM D, YYYY') : '—'
				}}</span>
				<span class="text-ink-gray-5">Target</span>
				<span class="text-ink-gray-8">{{
					moduleDoc.target_date ? dayjs(moduleDoc.target_date).format('MMM D, YYYY') : '—'
				}}</span>
				<span class="text-ink-gray-5">Done</span>
				<span class="text-ink-gray-8"
					>{{ moduleDoc.progress.completed }} of {{ moduleDoc.progress.total }}</span
				>
			</div>
			<div
				v-for="(n, g) in moduleDoc.progress.by_group"
				v-show="g !== 'Triage'"
				:key="g"
				class="flex items-center gap-2"
			>
				<StateIcon :group="g as StateGroup" />
				<span class="flex-1 text-ink-gray-6">{{ g }}</span>
				<span class="text-ink-gray-9">{{ n }}</span>
			</div>
		</aside>
	</div>
	<ModuleDialog v-model:open="dialogOpen" :project="project" :module="moduleDoc" @saved="load" />
</template>

<script setup lang="ts">
import { computed, onMounted, onScopeDispose, ref } from 'vue'
import { Badge, Button, dayjs } from 'frappe-ui'
import AppHeader from '@/components/common/AppHeader.vue'
import ModuleDialog from '@/components/common/ModuleDialog.vue'
import ProgressBar from '@/components/common/ProgressBar.vue'
import StateIcon from '@/components/common/StateIcon.vue'
import UserAvatar from '@/components/common/UserAvatar.vue'
import WorkItemsBoard from '@/components/workitem/WorkItemsBoard.vue'
import { api } from '@/api'
import { useDisplay } from '@/composables/useDisplay'
import { useWorkspace } from '@/stores/workspace'
import type { Module, StateGroup } from '@/types'
import { bus } from '@/utils/bus'
import { STATUS_THEME } from '@/utils/modules'

const props = defineProps<{ project: string; module: string }>()
const ws = useWorkspace()
const projectDoc = computed(() => ws.project(props.project))
const canEdit = computed(() => projectDoc.value?.role !== 'Guest')
const display = useDisplay(`module:${props.module}`)
const moduleDoc = ref<Module | null>(null)
const showStats = ref(true)
const dialogOpen = ref(false)

async function load() {
	moduleDoc.value = await api.module(props.module)
}
onMounted(load)
onScopeDispose(bus.on('item-updated', load))
</script>
