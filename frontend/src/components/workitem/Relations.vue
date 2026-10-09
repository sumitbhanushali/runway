<template>
	<section>
		<div class="mb-2 flex items-center gap-2">
			<h3 class="text-sm font-medium text-ink-gray-8">Relations</h3>
			<div v-if="editable" class="ml-auto flex items-center gap-1">
				<Select v-model="type" size="sm" class="w-36" :options="RELATION_TYPES" />
				<ItemSearch
					label="Add"
					:exclude="[item, ...relations.map((r) => r.item)]"
					@select="add"
				/>
			</div>
		</div>
		<div v-if="grouped.length" class="space-y-2">
			<div v-for="g in grouped" :key="g.type">
				<div class="mb-1 text-xs text-ink-gray-5">{{ g.label }}</div>
				<div
					v-for="r in g.items"
					:key="r.name + r.relation_type"
					class="group flex h-8 cursor-pointer items-center gap-2 rounded-3 px-2 hover:bg-surface-gray-1"
					@click="emit('open', r.item)"
				>
					<StateIcon :group="r.detail.state_group" />
					<span class="w-20 shrink-0 text-xs text-ink-gray-5">{{ r.item }}</span>
					<span class="flex-1 truncate text-sm text-ink-gray-8">{{
						r.detail.title
					}}</span>
					<button
						v-if="editable"
						type="button"
						class="invisible rounded-2 p-1 text-ink-gray-4 hover:bg-surface-gray-3 group-hover:visible"
						@click.stop="remove(r.name)"
					>
						<span class="lucide-x block size-3.5" />
					</button>
				</div>
			</div>
		</div>
		<div v-else class="text-sm text-ink-gray-4">No relations yet.</div>
	</section>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { Select, toast } from 'frappe-ui'
import StateIcon from '@/components/common/StateIcon.vue'
import ItemSearch from './ItemSearch.vue'
import { api, errorMessage } from '@/api'
import type { Relation, WorkItem } from '@/types'
import { RELATION_TYPES } from '@/utils/constants'

const props = defineProps<{ item: string; relations: Relation[]; editable: boolean }>()
const emit = defineEmits<{ open: [name: string]; changed: [] }>()

const type = ref('relates_to')

const grouped = computed(() =>
	RELATION_TYPES.map((t) => ({
		type: t.value,
		label: t.label,
		items: props.relations.filter((r) => r.relation_type === t.value),
	})).filter((g) => g.items.length),
)

async function add(other: WorkItem) {
	try {
		await api.addRelation(props.item, other.name, type.value)
		emit('changed')
	} catch (e) {
		toast.error(errorMessage(e))
	}
}

async function remove(name: string) {
	await api.removeRelation(name)
	emit('changed')
}
</script>
