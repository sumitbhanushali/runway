<template>
	<Popover align="end" :offset="4" bare>
		<template #trigger>
			<Button size="sm" icon-left="lucide-sliders-horizontal" label="Display" />
		</template>
		<template #default>
			<div
				class="w-80 space-y-3 rounded-4 bg-surface-elevation-2 p-3 shadow-2xl ring-1 ring-black/5"
			>
				<div
					v-if="layout !== 'spreadsheet'"
					class="flex items-center justify-between gap-2"
				>
					<span class="text-sm text-ink-gray-6">Group by</span>
					<Select v-model="display.group_by" class="w-40" :options="groupOptions" />
				</div>
				<div class="flex items-center justify-between gap-2">
					<span class="text-sm text-ink-gray-6">Order by</span>
					<Select v-model="display.order_by" class="w-40" :options="ORDER_BY_OPTIONS" />
				</div>
				<Switch v-model="display.show_sub_items" label="Show sub-work items" />
				<Switch
					v-if="layout !== 'spreadsheet'"
					v-model="display.show_empty_groups"
					label="Show empty groups"
				/>
				<div>
					<div class="mb-1.5 text-sm text-ink-gray-6">Display properties</div>
					<div class="flex flex-wrap gap-1">
						<button
							v-for="p in DISPLAY_PROPERTIES"
							:key="p.value"
							type="button"
							class="rounded-3 border px-2 py-0.5 text-xs"
							:class="
								properties.includes(p.value)
									? 'border-outline-gray-7 bg-surface-gray-7 text-ink-base'
									: 'border-outline-gray-2 text-ink-gray-6 hover:bg-surface-gray-2'
							"
							@click="toggleProperty(p.value)"
						>
							{{ p.label }}
						</button>
					</div>
				</div>
			</div>
		</template>
	</Popover>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Button, Popover, Select, Switch } from 'frappe-ui'
import type { DisplayFilters, DisplayProperty, Layout } from '@/types'
import { DISPLAY_PROPERTIES, GROUP_BY_OPTIONS, ORDER_BY_OPTIONS } from '@/utils/constants'

const props = defineProps<{ layout: Layout; singleProject: boolean }>()
const display = defineModel<DisplayFilters>('display', { required: true })
const properties = defineModel<DisplayProperty[]>('properties', { required: true })

const groupOptions = computed(() =>
	GROUP_BY_OPTIONS.filter(
		(o) =>
			props.singleProject ||
			['state_group', 'priority', 'assignees', 'none'].includes(o.value),
	),
)

function toggleProperty(p: DisplayProperty) {
	properties.value = properties.value.includes(p)
		? properties.value.filter((x) => x !== p)
		: [...properties.value, p]
}
</script>
