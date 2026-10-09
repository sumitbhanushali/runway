<template>
	<EmptyState
		v-if="missing"
		icon="lucide-file-question"
		title="Work item not found"
		description="It may have been deleted, or you no longer have access."
	/>
	<div v-else-if="!item" class="space-y-3 p-6">
		<div class="h-8 w-2/3 animate-pulse rounded-3 bg-surface-gray-2" />
		<div class="h-24 animate-pulse rounded-3 bg-surface-gray-2" />
	</div>
	<div v-else :class="layout === 'page' ? 'flex gap-8 p-6' : 'p-6'">
		<div class="min-w-0 flex-1 space-y-6">
			<div class="space-y-1">
				<button
					v-if="item.parent"
					type="button"
					class="flex items-center gap-1.5 text-sm text-ink-gray-5 hover:text-ink-gray-8"
					@click="openItem(item.parent.name)"
				>
					<StateIcon :group="item.parent.state_group" :size="12" />
					{{ item.parent.name }} · {{ item.parent.title }}
				</button>
				<div class="flex items-start gap-2">
					<textarea
						v-model="title"
						rows="1"
						class="w-full resize-none border-0 bg-transparent p-0 text-2xl font-semibold text-ink-gray-9 focus:ring-0"
						:readonly="!item.can_edit"
						@input="autoGrow"
						@blur="saveTitle"
						@keydown.enter.prevent="($event.target as HTMLTextAreaElement).blur()"
					/>
					<Dropdown :options="menu">
						<template #default>
							<Button variant="ghost" icon="lucide-ellipsis" />
						</template>
					</Dropdown>
				</div>
				<div
					v-if="item.archived_at"
					class="flex items-center gap-2 rounded-3 bg-surface-amber-1 px-3 py-1.5 text-sm text-ink-amber-6"
				>
					<span class="lucide-archive size-4" /> Archived
					{{ dayjs(item.archived_at).fromNow() }}
				</div>
				<div
					v-if="item.intake && item.state_group === 'Triage'"
					class="flex items-center gap-2 rounded-3 bg-surface-blue-1 px-3 py-1.5 text-sm text-ink-blue-6"
				>
					<span class="lucide-inbox size-4" /> In intake triage · {{ item.intake.status }}
				</div>
			</div>

			<div
				v-if="layout === 'peek'"
				class="grid grid-cols-[110px_1fr] items-center gap-x-3 gap-y-1"
			>
				<template v-for="p in visibleProps" :key="p.key">
					<span class="text-sm text-ink-gray-5">{{ p.label }}</span>
					<div>
						<ItemProperty
							:item="item"
							:prop="p.key"
							:editable="item.can_edit"
							@update="update"
						/>
					</div>
				</template>
			</div>

			<RichEditor
				v-model="description"
				kit="rich"
				:editable="item.can_edit"
				:bordered="false"
				:toolbar="false"
				placeholder="Add a description…"
				content-class="min-h-16 -mx-1 px-1"
				@focusout="saveDescription"
			/>

			<SubItems
				:parent="item.name"
				:project="item.project"
				:items="item.sub_items"
				:editable="item.can_edit"
				@open="openItem"
				@changed="load"
			/>
			<Relations
				:item="item.name"
				:relations="item.relations"
				:editable="item.can_edit"
				@open="openItem"
				@changed="load"
			/>
			<LinksAndFiles
				:item="item.name"
				:links="item.links"
				:attachments="item.attachments"
				:editable="item.can_edit"
				@changed="load"
			/>
			<ActivityTimeline
				:item="item.name"
				:project="item.project"
				:timeline="item.timeline"
				@changed="load"
			/>
		</div>

		<aside v-if="layout === 'page'" class="w-72 shrink-0 space-y-1">
			<div class="mb-3 flex items-center gap-2">
				<Button
					size="sm"
					:icon-left="item.is_subscribed ? 'lucide-bell-off' : 'lucide-bell'"
					:label="item.is_subscribed ? 'Unsubscribe' : 'Subscribe'"
					@click="toggleSubscription"
				/>
			</div>
			<div
				v-for="p in visibleProps"
				:key="p.key"
				class="grid grid-cols-[100px_1fr] items-center gap-2"
			>
				<span class="text-sm text-ink-gray-5">{{ p.label }}</span>
				<div>
					<ItemProperty
						:item="item"
						:prop="p.key"
						:editable="item.can_edit"
						@update="update"
					/>
				</div>
			</div>
			<div class="grid grid-cols-[100px_1fr] items-center gap-2 pt-2 text-sm">
				<span class="text-ink-gray-5">Created by</span>
				<span class="flex items-center gap-1.5 text-ink-gray-7"
					><UserAvatar :user="item.owner" size="xs" />{{ ws.userName(item.owner) }}</span
				>
				<span class="text-ink-gray-5">Created</span>
				<span class="text-ink-gray-7">{{
					dayjs(item.creation).format('MMM D, YYYY')
				}}</span>
			</div>
		</aside>
	</div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Button, Dropdown, dayjs, dialog, toast } from 'frappe-ui'
import EmptyState from '@/components/common/EmptyState.vue'
import RichEditor from '@/components/common/RichEditor.vue'
import StateIcon from '@/components/common/StateIcon.vue'
import UserAvatar from '@/components/common/UserAvatar.vue'
import ActivityTimeline from './ActivityTimeline.vue'
import ItemProperty from './ItemProperty.vue'
import LinksAndFiles from './LinksAndFiles.vue'
import Relations from './Relations.vue'
import SubItems from './SubItems.vue'
import { api, errorMessage } from '@/api'
import { useWorkspace } from '@/stores/workspace'
import type { WorkItem, WorkItemDetail } from '@/types'
import { bus } from '@/utils/bus'
import { onRealtime, subscribeDoc } from '@/utils/socket'

const props = withDefaults(defineProps<{ name: string; layout?: 'peek' | 'page' }>(), {
	layout: 'peek',
})
const emit = defineEmits<{ deleted: [] }>()

const ws = useWorkspace()
const route = useRoute()
const router = useRouter()
const item = ref<WorkItemDetail | null>(null)
const missing = ref(false)
const title = ref('')
const description = ref('')

const ALL_PROPS = [
	{ key: 'state', label: 'State' },
	{ key: 'priority', label: 'Priority' },
	{ key: 'assignees', label: 'Assignees' },
	{ key: 'labels', label: 'Labels' },
	{ key: 'start_date', label: 'Start date' },
	{ key: 'due_date', label: 'Due date' },
	{ key: 'estimate', label: 'Estimate' },
	{ key: 'cycle', label: 'Cycle' },
	{ key: 'modules', label: 'Modules' },
]
const visibleProps = computed(() => {
	const p = ws.project(item.value?.project)
	return ALL_PROPS.filter(
		(x) =>
			(x.key !== 'estimate' || p?.estimate_points.length) &&
			(x.key !== 'cycle' || p?.cycles_enabled) &&
			(x.key !== 'modules' || p?.modules_enabled),
	)
})

async function load() {
	try {
		const data = await api.detail(props.name)
		item.value = data
		title.value = data.title
		description.value = data.description ?? ''
		api.recordVisit('Runway Work Item', props.name).catch(() => {})
		missing.value = false
	} catch (e) {
		if (!item.value) missing.value = true
		else toast.error(errorMessage(e))
	}
}
watch(() => props.name, load, { immediate: true })

const unsubscribe = subscribeDoc('Runway Project', props.name.split('-')[0])
const off = onRealtime('runway_item_updated', (d: { name: string }) => {
	if (d.name === props.name) load()
})
onBeforeUnmount(() => {
	off()
	unsubscribe()
})

async function update(values: Partial<WorkItem>) {
	if (!item.value) return
	const before = { ...item.value }
	Object.assign(item.value, values)
	try {
		const row = await api.updateItem(props.name, values as Record<string, unknown>)
		bus.emit('item-updated', row)
		await load()
	} catch (e) {
		item.value = before
		toast.error(errorMessage(e))
	}
}

function saveTitle() {
	const t = title.value.trim()
	if (!item.value || !t || t === item.value.title) {
		if (item.value) title.value = item.value.title
		return
	}
	update({ title: t })
}

function saveDescription() {
	if (!item.value || description.value === (item.value.description ?? '')) return
	update({ description: description.value } as Partial<WorkItem>)
}

function autoGrow(e: Event) {
	const el = e.target as HTMLTextAreaElement
	el.style.height = 'auto'
	el.style.height = `${el.scrollHeight}px`
}

function openItem(name: string) {
	if (props.layout === 'page') router.push({ name: 'WorkItem', params: { item: name } })
	else router.push({ query: { ...route.query, peek: name } })
}

async function toggleSubscription() {
	if (!item.value) return
	item.value.is_subscribed = await api.toggleSubscription(props.name)
}

const menu = computed(() => {
	const i = item.value
	if (!i) return []
	const done = i.state_group === 'Completed' || i.state_group === 'Cancelled'
	return [
		{
			label: 'Copy link',
			icon: 'lucide-link',
			onClick: () => {
				navigator.clipboard.writeText(
					`${location.origin}/runway/${ws.workspace.value}/browse/${i.name}`,
				)
				toast.success('Link copied')
			},
		},
		{
			label: i.is_subscribed ? 'Unsubscribe' : 'Subscribe',
			icon: i.is_subscribed ? 'lucide-bell-off' : 'lucide-bell',
			onClick: toggleSubscription,
		},
		{
			label: 'Add sub-work item',
			icon: 'lucide-git-branch-plus',
			condition: () => i.can_edit,
			onClick: () =>
				bus.emit('create-item', { project: i.project, defaults: { parent_item: i.name } }),
		},
		{
			label: i.archived_at ? 'Restore' : 'Archive',
			icon: 'lucide-archive',
			condition: () => i.can_edit && (done || !!i.archived_at),
			onClick: archive,
		},
		{
			label: 'Delete',
			icon: 'lucide-trash-2',
			theme: 'red' as const,
			condition: () => i.can_edit,
			onClick: remove,
		},
	]
})

async function archive() {
	try {
		const row = await api.archiveItem(props.name, item.value?.archived_at ? 1 : 0)
		bus.emit('item-updated', row)
		await load()
	} catch (e) {
		toast.error(errorMessage(e))
	}
}

function remove() {
	dialog.danger({
		title: `Delete ${props.name}?`,
		message: 'The work item, its comments and activity will be removed permanently.',
		onConfirm: async ({ close }) => {
			await api.deleteItem(props.name)
			bus.emit('item-deleted', props.name)
			close()
			emit('deleted')
			if (props.layout === 'page') router.back()
		},
	})
}
</script>
