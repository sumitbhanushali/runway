<template>
	<div class="flex-1 overflow-y-auto">
		<section v-for="group in groups" :key="group.key">
			<div
				v-if="groups.length > 1 || group.key !== 'all'"
				class="sticky top-0 z-[1] flex h-10 items-center gap-2 border-b border-outline-gray-1 bg-surface-gray-1 px-4"
			>
				<button type="button" class="flex items-center gap-2" @click="toggle(group.key)">
					<span
						class="size-3.5 text-ink-gray-5 transition-transform"
						:class="
							collapsed[group.key] ? 'lucide-chevron-right' : 'lucide-chevron-down'
						"
					/>
					<GroupMark :group="group" />
					<span class="text-sm font-medium text-ink-gray-8">{{ group.label }}</span>
					<span class="text-sm text-ink-gray-5">{{ group.items.length }}</span>
				</button>
				<button
					v-if="canCreate"
					type="button"
					class="ml-auto rounded-3 p-1 text-ink-gray-5 hover:bg-surface-gray-3"
					@click="emit('create-in', group)"
				>
					<span class="lucide-plus block size-4" />
				</button>
			</div>
			<template v-if="!collapsed[group.key]">
				<div
					v-for="item in group.items"
					:key="item.name"
					class="group/row flex min-h-11 cursor-pointer items-center gap-3 border-b border-outline-gray-1 px-4 py-1.5 hover:bg-surface-gray-1"
					:class="{ 'bg-surface-gray-2': selected === item.name }"
					@click="emit('open', item)"
				>
					<span
						v-if="properties.includes('id')"
						class="w-20 shrink-0 text-sm text-ink-gray-5"
						>{{ item.name }}</span
					>
					<ItemProperty
						v-if="properties.includes('state') && groupBy !== 'state'"
						:item="item"
						prop="state"
						compact
						:editable="editable(item)"
						@update="(v) => emit('update', item.name, v)"
						@click.stop
					/>
					<span class="min-w-0 flex-1 truncate text-sm text-ink-gray-9">
						<span v-if="item.parent_item" class="mr-1 text-ink-gray-4"
							>{{ item.parent_item }} ›</span
						>
						{{ item.title }}
					</span>
					<ItemProperties
						:item="item"
						:properties="properties"
						:editable="editable(item)"
						:hide="hiddenFor"
						class="shrink-0 justify-end"
						@update="(v) => emit('update', item.name, v)"
					/>
				</div>
				<QuickAdd
					v-if="canCreate"
					:project-identifier="projectIdentifier"
					:create="(t: string) => createIn(group, t)"
					form-class="border-b border-outline-gray-1"
				/>
			</template>
		</section>
	</div>
</template>

<script setup lang="ts">
import { computed, reactive } from 'vue'
import GroupMark from './GroupMark.vue'
import ItemProperties from './ItemProperties.vue'
import QuickAdd from './QuickAdd.vue'
import ItemProperty from '@/components/workitem/ItemProperty.vue'
import type { DisplayProperty, GroupBy, WorkItem } from '@/types'
import type { ItemGroup } from '@/utils/grouping'

const props = defineProps<{
	groups: ItemGroup[]
	groupBy: GroupBy
	properties: DisplayProperty[]
	editable: (item: WorkItem) => boolean
	canCreate: boolean
	projectIdentifier?: string
	selected?: string | null
	create: (defaults: Partial<WorkItem>, title: string) => Promise<unknown>
}>()
const emit = defineEmits<{
	open: [item: WorkItem]
	update: [name: string, values: Partial<WorkItem>]
	'create-in': [group: ItemGroup]
}>()

const collapsed = reactive<Record<string, boolean>>({})
function toggle(key: string) {
	collapsed[key] = !collapsed[key]
}

const hiddenFor = computed(() => ['state', props.groupBy === 'priority' ? 'priority' : ''])

function createIn(group: ItemGroup, title: string) {
	return props.create(group.defaults, title)
}
</script>
