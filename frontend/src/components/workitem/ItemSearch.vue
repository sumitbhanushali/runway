<template>
	<Popover v-model:open="open" align="start" :offset="4" bare>
		<template #trigger>
			<slot name="trigger">
				<Button size="sm" variant="ghost" :icon-left="icon" :label="label" />
			</slot>
		</template>
		<template #default>
			<div class="w-96 rounded-4 bg-surface-elevation-2 p-1 shadow-2xl ring-1 ring-black/5">
				<input
					ref="input"
					v-model="query"
					class="mb-1 h-8 w-full rounded-3 border-0 bg-surface-gray-2 px-2 text-sm placeholder-ink-gray-4 focus:ring-0"
					placeholder="Search by ID or title…"
				/>
				<div class="max-h-72 overflow-y-auto">
					<button
						v-for="r in results"
						:key="r.name"
						type="button"
						class="flex w-full items-center gap-2 rounded-3 px-2 py-1.5 text-left text-sm hover:bg-surface-gray-2"
						@click="pick(r)"
					>
						<StateIcon :group="r.state_group" />
						<span class="w-20 shrink-0 text-ink-gray-5">{{ r.name }}</span>
						<span class="truncate text-ink-gray-8">{{ r.title }}</span>
					</button>
					<div
						v-if="!results.length"
						class="px-2 py-3 text-center text-sm text-ink-gray-4"
					>
						{{ loading ? 'Searching…' : 'No work items found' }}
					</div>
				</div>
			</div>
		</template>
	</Popover>
</template>

<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'
import { Button, Popover, debounce } from 'frappe-ui'
import StateIcon from '@/components/common/StateIcon.vue'
import { api } from '@/api'
import { useWorkspace } from '@/stores/workspace'
import type { WorkItem } from '@/types'

const props = withDefaults(
	defineProps<{ label?: string; icon?: string; project?: string; exclude?: string[] }>(),
	{ label: 'Add', icon: 'lucide-plus', exclude: () => [] },
)
const emit = defineEmits<{ select: [item: WorkItem] }>()

const ws = useWorkspace()
const open = ref(false)
const query = ref('')
const results = ref<WorkItem[]>([])
const loading = ref(false)
const input = ref<HTMLInputElement | null>(null)

const search = debounce(async () => {
	loading.value = true
	try {
		const rows = await api.searchItems(query.value, ws.workspace.value, props.project)
		results.value = rows.filter((r) => !props.exclude.includes(r.name))
	} finally {
		loading.value = false
	}
}, 200)

watch(query, search)
watch(open, async (v) => {
	if (!v) return
	query.value = ''
	search()
	await nextTick()
	input.value?.focus()
})

function pick(item: WorkItem) {
	emit('select', item)
	open.value = false
}
</script>
