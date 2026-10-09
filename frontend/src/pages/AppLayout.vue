<template>
	<div class="flex h-full overflow-hidden">
		<AppSidebar @search="paletteOpen = true" />
		<main class="flex min-w-0 flex-1 flex-col overflow-hidden">
			<router-view :key="$route.path" />
		</main>
		<WorkItemPeek />
		<CreateWorkItemDialog />
		<CommandPalette v-model:open="paletteOpen" />
	</div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { toast } from 'frappe-ui'
import AppSidebar from '@/components/shell/AppSidebar.vue'
import CommandPalette from '@/components/shell/CommandPalette.vue'
import CreateWorkItemDialog from '@/components/workitem/CreateWorkItemDialog.vue'
import WorkItemPeek from '@/components/workitem/WorkItemPeek.vue'
import { api } from '@/api'
import { useWorkspace } from '@/stores/workspace'
import { bus } from '@/utils/bus'
import { onRealtime } from '@/utils/socket'

defineProps<{ workspace: string }>()

const ws = useWorkspace()
const paletteOpen = ref(false)

function isTyping(e: KeyboardEvent) {
	const el = e.target as HTMLElement | null
	return !!el && (el.isContentEditable || ['INPUT', 'TEXTAREA', 'SELECT'].includes(el.tagName))
}

function onKey(e: KeyboardEvent) {
	if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
		e.preventDefault()
		paletteOpen.value = true
		return
	}
	if (isTyping(e) || e.metaKey || e.ctrlKey || e.altKey) return
	if (e.key === 'c') {
		e.preventDefault()
		bus.emit('create-item', {})
	}
}

let off: (() => void) | undefined
onMounted(() => {
	window.addEventListener('keydown', onKey)
	off = onRealtime('runway_notification', async () => {
		ws.setUnread(await api.unreadCount())
		toast.info('New notification in your inbox')
	})
})
onBeforeUnmount(() => {
	window.removeEventListener('keydown', onKey)
	off?.()
})
</script>
