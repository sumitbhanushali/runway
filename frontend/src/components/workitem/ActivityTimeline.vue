<template>
	<section>
		<div class="mb-3 flex items-center gap-2">
			<h3 class="text-sm font-medium text-ink-gray-8">Activity</h3>
			<TabButtons v-model="filter" class="ml-auto" size="sm" :options="filterOptions" />
		</div>
		<ol class="space-y-3">
			<li v-for="entry in shown" :key="entry.kind + entry.name" class="flex gap-3">
				<template v-if="entry.kind === 'activity'">
					<span
						class="mt-0.5 flex size-6 shrink-0 items-center justify-center rounded-full bg-surface-gray-2"
					>
						<span :class="activityIcon(entry)" class="size-3.5 text-ink-gray-5" />
					</span>
					<p class="pt-0.5 text-sm text-ink-gray-6">
						<span class="font-medium text-ink-gray-8">{{
							ws.userName(entry.actor)
						}}</span>
						{{ describe(entry) }}
						<span class="text-ink-gray-4">· {{ ago(entry.creation) }}</span>
					</p>
				</template>
				<template v-else>
					<UserAvatar :user="entry.owner!" size="sm" />
					<div class="min-w-0 flex-1 rounded-4 border border-outline-gray-1">
						<div
							class="flex items-center gap-2 border-b border-outline-gray-1 bg-surface-gray-1 px-3 py-1.5 text-sm"
						>
							<span class="font-medium text-ink-gray-8">{{
								ws.userName(entry.owner)
							}}</span>
							<span class="text-ink-gray-4">{{ ago(entry.creation) }}</span>
							<span v-if="entry.edited_at" class="text-xs text-ink-gray-4"
								>(edited)</span
							>
							<Badge
								v-if="entry.access === 'External'"
								size="sm"
								theme="blue"
								label="External"
							/>
							<Dropdown
								v-if="entry.owner === me"
								class="ml-auto"
								:options="[
									{
										label: 'Edit',
										icon: 'lucide-pencil',
										onClick: () => startEdit(entry),
									},
									{
										label: 'Delete',
										icon: 'lucide-trash-2',
										theme: 'red',
										onClick: () => remove(entry.name),
									},
								]"
							>
								<template #default>
									<button
										type="button"
										class="rounded-2 p-0.5 text-ink-gray-5 hover:bg-surface-gray-3"
									>
										<span class="lucide-ellipsis block size-4" />
									</button>
								</template>
							</Dropdown>
						</div>
						<div class="px-3 py-2">
							<RichEditor
								v-if="editing === entry.name"
								v-model="editContent"
								submit-on-mod-enter
								@submit="saveEdit(entry.name)"
							>
								<template #actions>
									<div class="flex gap-1">
										<Button size="sm" label="Cancel" @click="editing = null" />
										<Button
											size="sm"
											variant="solid"
											label="Save"
											@click="saveEdit(entry.name)"
										/>
									</div>
								</template>
							</RichEditor>
							<!-- eslint-disable-next-line vue/no-v-html -- Text Editor fields are sanitized by Frappe on save -->
							<div v-else class="runway-prose" v-html="entry.content" />
							<div class="mt-2 flex flex-wrap items-center gap-1">
								<button
									v-for="r in reactionSummary(entry)"
									:key="r.emoji"
									type="button"
									class="flex items-center gap-1 rounded-full border px-1.5 text-xs"
									:class="
										r.mine
											? 'border-outline-blue-3 bg-surface-blue-1'
											: 'border-outline-gray-2'
									"
									:title="r.users.map((u) => ws.userName(u)).join(', ')"
									@click="react(entry.name, r.emoji)"
								>
									{{ r.emoji }} {{ r.users.length }}
								</button>
								<Dropdown
									:options="
										REACTIONS.map((e) => ({
											label: e,
											onClick: () => react(entry.name, e),
										}))
									"
								>
									<template #default>
										<button
											type="button"
											class="rounded-full p-1 text-ink-gray-4 hover:bg-surface-gray-2"
										>
											<span class="lucide-smile-plus block size-3.5" />
										</button>
									</template>
								</Dropdown>
							</div>
						</div>
					</div>
				</template>
			</li>
		</ol>
		<div class="mt-4 flex gap-3">
			<UserAvatar :user="me" size="sm" />
			<div class="flex-1">
				<RichEditor
					v-model="draft"
					placeholder="Add a comment… use @ to mention"
					submit-on-mod-enter
					:mention-users="mentionUsers"
					@submit="submit"
				>
					<template #actions="{ isEmpty }">
						<div class="flex items-center gap-2">
							<Select
								v-model="access"
								size="sm"
								class="w-28"
								:options="['Internal', 'External']"
							/>
							<Button
								size="sm"
								variant="solid"
								label="Comment"
								:loading="posting"
								:disabled="isEmpty"
								@click="submit"
							/>
						</div>
					</template>
				</RichEditor>
			</div>
		</div>
	</section>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { Badge, Button, Dropdown, Select, TabButtons, dayjs, toast } from 'frappe-ui'
import RichEditor from '@/components/common/RichEditor.vue'
import UserAvatar from '@/components/common/UserAvatar.vue'
import { api, errorMessage } from '@/api'
import { useProjectOptions } from '@/composables/useProjectOptions'
import { useWorkspace } from '@/stores/workspace'
import type { TimelineEntry } from '@/types'
import { REACTIONS, RELATION_TYPES } from '@/utils/constants'

const props = defineProps<{ item: string; project: string; timeline: TimelineEntry[] }>()
const emit = defineEmits<{ changed: [] }>()

const ws = useWorkspace()
const opts = useProjectOptions(computed(() => props.project))
const me = computed(() => ws.user.value?.name ?? '')
const mentionUsers = computed(() => opts.project.value?.members.map((m) => m.user))

const filter = ref<'all' | 'comments' | 'updates'>('all')
const filterOptions = [
	{ value: 'all', label: 'All' },
	{ value: 'comments', label: 'Comments' },
	{ value: 'updates', label: 'Updates' },
]
const shown = computed(() =>
	props.timeline.filter((e) =>
		filter.value === 'all'
			? true
			: filter.value === 'comments'
				? e.kind === 'comment'
				: e.kind === 'activity',
	),
)

const draft = ref('')
const access = ref<'Internal' | 'External'>('Internal')
const posting = ref(false)
const editing = ref<string | null>(null)
const editContent = ref('')

const FIELD_LABELS: Record<string, string> = {
	title: 'title',
	description: 'description',
	state: 'state',
	priority: 'priority',
	start_date: 'start date',
	due_date: 'due date',
	parent_item: 'parent',
	estimate_point: 'estimate',
	cycle: 'cycle',
	assignees: 'assignees',
	labels: 'labels',
	modules: 'modules',
	archived_at: 'archive',
	is_draft: 'draft',
}

function display(field: string | undefined, value: string | null | undefined): string {
	if (!value) return 'none'
	switch (field) {
		case 'state':
			return opts.stateOf(value)?.title ?? value
		case 'cycle':
			return opts.cycleOf(value)?.title ?? value
		case 'assignees':
			return value
				.split(', ')
				.map((u) => ws.userName(u))
				.join(', ')
		case 'labels':
			return value
				.split(', ')
				.map((l) => opts.labelOf(l)?.title ?? l)
				.join(', ')
		case 'modules':
			return value
				.split(', ')
				.map((m) => opts.moduleOf(m)?.title ?? m)
				.join(', ')
		case 'start_date':
		case 'due_date':
			return dayjs(value).format('MMM D, YYYY')
		default:
			return value
	}
}

function describe(e: TimelineEntry): string {
	if (e.verb === 'created') return 'created the work item'
	if (e.verb === 'added_relation')
		return `marked as ${RELATION_TYPES.find((r) => r.value === e.field)?.label.toLowerCase() ?? e.field} ${e.new_value}`
	if (e.verb === 'removed_relation') return `removed relation with ${e.old_value}`
	if (e.verb === 'added_link') return `added a link ${e.new_value}`
	if (e.verb === 'removed_link') return `removed a link ${e.old_value}`
	if (e.verb === 'added_attachment') return `attached ${e.new_value}`
	if (e.verb === 'removed_attachment') return `removed attachment ${e.old_value}`
	const label = FIELD_LABELS[e.field ?? ''] ?? e.field
	if (e.field === 'description') return 'updated the description'
	if (e.field === 'archived_at')
		return e.new_value ? 'archived the work item' : 'restored the work item'
	if (!e.new_value) return `removed the ${label} ${display(e.field, e.old_value)}`
	return `set the ${label} to ${display(e.field, e.new_value)}`
}

function activityIcon(e: TimelineEntry) {
	const icons: Record<string, string> = {
		state: 'lucide-circle-dot',
		priority: 'lucide-signal',
		assignees: 'lucide-users',
		labels: 'lucide-tag',
		cycle: 'lucide-refresh-ccw',
		modules: 'lucide-boxes',
		due_date: 'lucide-calendar',
		start_date: 'lucide-calendar',
	}
	if (e.verb === 'created') return 'lucide-sparkles'
	if (e.verb?.includes('link')) return 'lucide-link'
	if (e.verb?.includes('relation')) return 'lucide-git-compare'
	if (e.verb?.includes('attachment')) return 'lucide-paperclip'
	return icons[e.field ?? ''] ?? 'lucide-pencil'
}

function ago(ts: string) {
	return dayjs(ts).fromNow()
}

function reactionSummary(e: TimelineEntry) {
	const map = new Map<string, string[]>()
	for (const r of e.reactions ?? []) map.set(r.emoji, [...(map.get(r.emoji) ?? []), r.user])
	return [...map.entries()].map(([emoji, users]) => ({
		emoji,
		users,
		mine: users.includes(me.value),
	}))
}

async function submit() {
	if (!draft.value.trim()) return
	posting.value = true
	try {
		await api.addComment(props.item, draft.value, access.value)
		draft.value = ''
		emit('changed')
	} catch (e) {
		toast.error(errorMessage(e))
	} finally {
		posting.value = false
	}
}

function startEdit(e: TimelineEntry) {
	editing.value = e.name
	editContent.value = e.content ?? ''
}

async function saveEdit(name: string) {
	await api.updateComment(name, editContent.value)
	editing.value = null
	emit('changed')
}

async function remove(name: string) {
	await api.deleteComment(name)
	emit('changed')
}

async function react(name: string, emoji: string) {
	await api.toggleReaction(name, emoji)
	emit('changed')
}
</script>
