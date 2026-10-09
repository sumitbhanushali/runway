<template>
	<Dialog v-model:open="open" size="xl" position="top" bare>
		<template #default>
			<div
				class="overflow-hidden rounded-6 bg-surface-elevation-2"
				@keydown.down.prevent="move(1)"
				@keydown.up.prevent="move(-1)"
				@keydown.enter.prevent="go(active)"
			>
				<div class="flex items-center gap-2 border-b border-outline-gray-1 px-4">
					<span class="lucide-search size-4 text-ink-gray-5" />
					<input
						ref="input"
						v-model="query"
						class="h-12 flex-1 border-0 bg-transparent px-0 text-base text-ink-gray-9 placeholder-ink-gray-4 focus:ring-0"
						placeholder="Search work items, projects, pages or actions…"
					/>
				</div>
				<div class="max-h-96 overflow-y-auto p-2">
					<template v-for="section in sections" :key="section.title">
						<div
							v-if="section.entries.length"
							class="px-2 pb-1 pt-2 text-xs font-medium text-ink-gray-5"
						>
							{{ section.title }}
						</div>
						<button
							v-for="entry in section.entries"
							:key="entry.key"
							type="button"
							class="flex w-full items-center gap-2 rounded-4 px-2 py-2 text-left text-sm"
							:class="
								flat.indexOf(entry) === active
									? 'bg-surface-gray-3'
									: 'hover:bg-surface-gray-2'
							"
							@mouseenter="active = flat.indexOf(entry)"
							@click="go(flat.indexOf(entry))"
						>
							<span :class="entry.icon" class="size-4 text-ink-gray-5" />
							<span v-if="entry.hint" class="w-20 shrink-0 text-ink-gray-5">{{
								entry.hint
							}}</span>
							<span class="truncate text-ink-gray-8">{{ entry.label }}</span>
						</button>
					</template>
					<div v-if="!flat.length" class="px-2 py-6 text-center text-sm text-ink-gray-4">
						No results
					</div>
				</div>
			</div>
		</template>
	</Dialog>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { useRouter, type RouteLocationRaw } from 'vue-router'
import { Dialog, debounce } from 'frappe-ui'
import { api } from '@/api'
import { useWorkspace } from '@/stores/workspace'
import type { WorkItem } from '@/types'
import { bus } from '@/utils/bus'

interface Entry {
	key: string
	label: string
	icon: string
	hint?: string
	run: () => void
}

const open = defineModel<boolean>('open', { default: false })
const ws = useWorkspace()
const router = useRouter()
const query = ref('')
const items = ref<WorkItem[]>([])
const active = ref(0)
const input = ref<HTMLInputElement | null>(null)

const nav = (to: RouteLocationRaw) => () => router.push(to)

const sections = computed(() => {
	const q = query.value.trim().toLowerCase()
	const match = (s: string) => !q || s.toLowerCase().includes(q)
	const actions: Entry[] = [
		{
			key: 'new',
			label: 'Create work item',
			icon: 'lucide-square-pen',
			run: () => bus.emit('create-item', {}),
		},
		{
			key: 'new-project',
			label: 'Create project',
			icon: 'lucide-folder-plus',
			run: nav({ name: 'Projects', query: { create: '1' } }),
		},
		{ key: 'home', label: 'Go to Home', icon: 'lucide-house', run: nav({ name: 'Home' }) },
		{ key: 'inbox', label: 'Go to Inbox', icon: 'lucide-inbox', run: nav({ name: 'Inbox' }) },
		{
			key: 'mywork',
			label: 'Go to Your work',
			icon: 'lucide-user-check',
			run: nav({ name: 'MyWork' }),
		},
		{
			key: 'analytics',
			label: 'Go to Analytics',
			icon: 'lucide-chart-column',
			run: nav({ name: 'Analytics' }),
		},
	].filter((a) => match(a.label))
	const projects: Entry[] = ws.projects.value
		.filter((p) => match(p.title) || match(p.identifier))
		.map((p) => ({
			key: `p-${p.name}`,
			label: p.title,
			hint: p.identifier,
			icon: 'lucide-folder',
			run: nav({ name: 'ProjectItems', params: { project: p.name } }),
		}))
	const workItems: Entry[] = items.value.map((i) => ({
		key: `i-${i.name}`,
		label: i.title,
		hint: i.name,
		icon: 'lucide-circle-dot',
		run: nav({ name: 'WorkItem', params: { item: i.name } }),
	}))
	return [
		{ title: 'Work items', entries: workItems },
		{ title: 'Projects', entries: projects.slice(0, 6) },
		{ title: 'Actions', entries: actions },
	]
})
const flat = computed(() => sections.value.flatMap((s) => s.entries))

const search = debounce(async () => {
	if (!query.value.trim()) {
		items.value = []
		return
	}
	items.value = (await api.searchItems(query.value, ws.workspace.value)).slice(0, 8)
}, 200)

watch(query, () => {
	active.value = 0
	search()
})
watch(open, async (v) => {
	if (!v) return
	query.value = ''
	items.value = []
	await nextTick()
	input.value?.focus()
})

function move(d: number) {
	const n = flat.value.length
	if (n) active.value = (active.value + d + n) % n
}

function go(i: number) {
	const entry = flat.value[i]
	if (!entry) return
	open.value = false
	entry.run()
}
</script>
