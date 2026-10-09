<template>
	<Transition
		enter-from-class="translate-x-full"
		enter-active-class="transition-transform duration-150"
		leave-to-class="translate-x-full"
		leave-active-class="transition-transform duration-150"
	>
		<aside
			v-if="name"
			class="fixed inset-y-0 right-0 z-20 flex w-full max-w-3xl flex-col border-l border-outline-gray-2 bg-surface-base shadow-2xl"
		>
			<div class="flex h-12 shrink-0 items-center gap-2 border-b border-outline-gray-1 px-4">
				<Button variant="ghost" icon="lucide-x" tooltip="Close (Esc)" @click="close" />
				<Button
					variant="ghost"
					icon="lucide-maximize-2"
					tooltip="Open full page"
					@click="expand"
				/>
				<span class="text-sm text-ink-gray-5">{{ name }}</span>
			</div>
			<div class="min-h-0 flex-1 overflow-y-auto">
				<WorkItemDetail :key="name" :name="name" layout="peek" @deleted="close" />
			</div>
		</aside>
	</Transition>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Button } from 'frappe-ui'
import WorkItemDetail from './WorkItemDetail.vue'

const route = useRoute()
const router = useRouter()
const name = computed(() => (route.query.peek as string) || null)

function close() {
	const query = { ...route.query }
	delete query.peek
	router.replace({ query })
}

function expand() {
	if (name.value) router.push({ name: 'WorkItem', params: { item: name.value } })
}

function onKey(e: KeyboardEvent) {
	if (e.key !== 'Escape' || !name.value) return
	// Leave Escape to an open dialog or popover first.
	if (
		document.querySelector(
			'[role="dialog"][data-state="open"], [data-slot="content"][data-state="open"]',
		)
	)
		return
	close()
}
onMounted(() => window.addEventListener('keydown', onKey))
onBeforeUnmount(() => window.removeEventListener('keydown', onKey))
</script>
