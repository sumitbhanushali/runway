<template>
	<AppHeader :crumbs="crumbs" />
	<div class="flex-1 overflow-y-auto">
		<div class="mx-auto max-w-6xl">
			<WorkItemDetail :key="item" :name="item" layout="page" />
		</div>
	</div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import AppHeader from '@/components/common/AppHeader.vue'
import WorkItemDetail from '@/components/workitem/WorkItemDetail.vue'
import { useWorkspace } from '@/stores/workspace'

const props = defineProps<{ item: string }>()
const ws = useWorkspace()
const project = computed(() => props.item.split('-')[0])
const crumbs = computed(() => [
	{
		label: ws.project(project.value)?.title ?? project.value,
		route: { name: 'ProjectItems', params: { project: project.value } },
	},
	{ label: 'Work items', route: { name: 'ProjectItems', params: { project: project.value } } },
	{ label: props.item },
])
</script>
