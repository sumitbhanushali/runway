<template>
	<AppHeader :crumbs="[{ label: 'Your work', icon: 'lucide-user-check' }]">
		<template #actions>
			<TabButtons
				:model-value="current"
				:options="tabs"
				size="sm"
				@update:model-value="(t) => router.replace({ params: { tab: String(t) } })"
			/>
		</template>
	</AppHeader>
	<WorkItemsBoard
		:key="current"
		:state="display"
		:my-work="current"
		:hide-filters="
			current === 'assigned' ? ['assignees'] : current === 'created' ? ['owner'] : []
		"
		:empty-title="emptyTitle"
	/>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { TabButtons } from 'frappe-ui'
import AppHeader from '@/components/common/AppHeader.vue'
import WorkItemsBoard from '@/components/workitem/WorkItemsBoard.vue'
import { useDisplay } from '@/composables/useDisplay'

const props = defineProps<{ tab?: string }>()
const router = useRouter()
const current = computed(() => props.tab || 'assigned')
const tabs = [
	{ value: 'assigned', label: 'Assigned' },
	{ value: 'created', label: 'Created' },
	{ value: 'subscribed', label: 'Subscribed' },
]
const display = useDisplay('my-work', {
	display: {
		layout: 'list',
		group_by: 'state_group',
		order_by: '-modified',
		show_sub_items: true,
		show_empty_groups: false,
	},
})
const emptyTitle = computed(() =>
	current.value === 'assigned'
		? 'Nothing assigned to you'
		: current.value === 'created'
			? 'You have not created any work items'
			: 'No subscriptions yet',
)
</script>
