<template>
	<section>
		<div class="mb-2 flex items-center gap-2">
			<h3 class="text-sm font-medium text-ink-gray-8">Sub-work items</h3>
			<span v-if="items.length" class="text-xs text-ink-gray-5"
				>{{ done }}/{{ items.length }} done</span
			>
			<div
				v-if="items.length"
				class="h-1.5 w-24 overflow-hidden rounded-full bg-surface-gray-3"
			>
				<div
					class="h-full bg-surface-green-6"
					:style="{ width: `${(done / items.length) * 100}%` }"
				/>
			</div>
			<div v-if="editable" class="ml-auto flex gap-1">
				<ItemSearch
					label="Add existing"
					icon="lucide-link-2"
					:project="project"
					:exclude="[parent, ...items.map((i) => i.name)]"
					@select="attach"
				/>
			</div>
		</div>
		<div v-if="items.length" class="overflow-hidden rounded-4 border border-outline-gray-1">
			<div
				v-for="item in items"
				:key="item.name"
				class="flex h-9 cursor-pointer items-center gap-2 border-b border-outline-gray-1 px-3 last:border-b-0 hover:bg-surface-gray-1"
				@click="emit('open', item.name)"
			>
				<ItemProperty
					:item="item"
					prop="state"
					compact
					:editable="editable"
					@update="(v) => update(item, v)"
				/>
				<span class="w-16 shrink-0 text-xs text-ink-gray-5">{{ item.name }}</span>
				<span class="flex-1 truncate text-sm text-ink-gray-8">{{ item.title }}</span>
				<ItemProperty
					:item="item"
					prop="priority"
					compact
					:editable="editable"
					@update="(v) => update(item, v)"
				/>
				<ItemProperty
					:item="item"
					prop="assignees"
					compact
					:editable="editable"
					@update="(v) => update(item, v)"
				/>
				<button
					v-if="editable"
					type="button"
					class="rounded-2 p-1 text-ink-gray-4 hover:bg-surface-gray-3 hover:text-ink-gray-7"
					title="Remove from parent"
					@click.stop="update(item, { parent_item: null })"
				>
					<span class="lucide-unlink block size-3.5" />
				</button>
			</div>
		</div>
		<QuickAdd v-if="editable" :create="createChild" button-class="!px-0" form-class="!px-0" />
	</section>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { toast } from 'frappe-ui'
import QuickAdd from '@/components/layouts/QuickAdd.vue'
import ItemProperty from './ItemProperty.vue'
import ItemSearch from './ItemSearch.vue'
import { api, errorMessage } from '@/api'
import type { WorkItem } from '@/types'
import { bus } from '@/utils/bus'

const props = defineProps<{
	parent: string
	project: string
	items: WorkItem[]
	editable: boolean
}>()
const emit = defineEmits<{ open: [name: string]; changed: [] }>()

const done = computed(
	() =>
		props.items.filter((i) => i.state_group === 'Completed' || i.state_group === 'Cancelled')
			.length,
)

async function update(item: WorkItem, values: Partial<WorkItem>) {
	try {
		const row = await api.updateItem(item.name, values as Record<string, unknown>)
		bus.emit('item-updated', row)
		emit('changed')
	} catch (e) {
		toast.error(errorMessage(e))
	}
}

async function createChild(title: string) {
	const row = await api.createItem(props.project, { title, parent_item: props.parent })
	bus.emit('item-created', row)
	emit('changed')
}

function attach(item: WorkItem) {
	if (item.project !== props.project) {
		toast.error('Sub-work items must be in the same project')
		return
	}
	update(item, { parent_item: props.parent })
}
</script>
