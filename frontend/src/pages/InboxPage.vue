<template>
	<AppHeader :crumbs="[{ label: 'Inbox', icon: 'lucide-inbox' }]">
		<template #actions>
			<TabButtons v-model="tab" :options="tabs" size="sm" />
			<Button
				size="sm"
				icon-left="lucide-check-check"
				label="Mark all read"
				@click="markAll"
			/>
		</template>
	</AppHeader>
	<div class="flex-1 overflow-y-auto">
		<div v-if="loading && !rows.length" class="space-y-2 p-4">
			<div v-for="i in 5" :key="i" class="h-14 animate-pulse rounded-3 bg-surface-gray-2" />
		</div>
		<EmptyState
			v-else-if="!rows.length"
			icon="lucide-inbox"
			title="You're all caught up"
			description="Assignments, mentions and updates on items you follow land here."
		/>
		<div
			v-for="n in rows"
			:key="n.name"
			class="group flex cursor-pointer items-start gap-3 border-b border-outline-gray-1 px-6 py-3 hover:bg-surface-gray-1"
			@click="open(n)"
		>
			<span
				class="mt-2 size-2 shrink-0 rounded-full"
				:class="n.read_at ? 'bg-transparent' : 'bg-surface-blue-5'"
			/>
			<UserAvatar v-if="n.actor" :user="n.actor" size="md" />
			<div class="min-w-0 flex-1">
				<div class="text-sm text-ink-gray-8">
					<span class="font-medium">{{ ws.userName(n.actor) }}</span> {{ n.message }}
				</div>
				<div class="mt-0.5 flex items-center gap-2 text-xs text-ink-gray-5">
					<span :class="ICONS[n.notification_type] ?? 'lucide-bell'" class="size-3" />
					<span v-if="n.item">{{ n.item.name }} · {{ n.item.title }}</span>
					<span>· {{ dayjs(n.creation).fromNow() }}</span>
					<span v-if="n.snoozed_until && tab === 'snoozed'"
						>· until {{ dayjs(n.snoozed_until).format('MMM D, h:mm a') }}</span
					>
				</div>
			</div>
			<div class="invisible flex gap-1 group-hover:visible" @click.stop>
				<Button
					size="sm"
					variant="ghost"
					:icon="n.read_at ? 'lucide-mail' : 'lucide-mail-open'"
					:tooltip="n.read_at ? 'Mark unread' : 'Mark read'"
					@click="toggleRead(n)"
				/>
				<Dropdown :options="snoozeOptions(n)">
					<template #default
						><Button
							size="sm"
							variant="ghost"
							icon="lucide-alarm-clock"
							tooltip="Snooze"
					/></template>
				</Dropdown>
				<Button
					size="sm"
					variant="ghost"
					:icon="n.archived_at ? 'lucide-archive-restore' : 'lucide-archive'"
					:tooltip="n.archived_at ? 'Unarchive' : 'Archive'"
					@click="archive(n)"
				/>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Button, Dropdown, TabButtons, dayjs } from 'frappe-ui'
import AppHeader from '@/components/common/AppHeader.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import UserAvatar from '@/components/common/UserAvatar.vue'
import { api } from '@/api'
import { useWorkspace } from '@/stores/workspace'
import type { Notification } from '@/types'
import { onRealtime } from '@/utils/socket'

const ICONS: Record<string, string> = {
	assigned: 'lucide-user-plus',
	mentioned: 'lucide-at-sign',
	state_changed: 'lucide-circle-dot',
	commented: 'lucide-message-square',
	updated: 'lucide-pencil',
	intake: 'lucide-inbox',
}

const ws = useWorkspace()
const router = useRouter()
const tab = ref('all')
const tabs = [
	{ value: 'all', label: 'All' },
	{ value: 'unread', label: 'Unread' },
	{ value: 'snoozed', label: 'Snoozed' },
	{ value: 'archived', label: 'Archived' },
]
const rows = ref<Notification[]>([])
const loading = ref(false)

async function load() {
	loading.value = true
	try {
		rows.value = await api.inbox(tab.value)
		ws.setUnread(await api.unreadCount())
	} finally {
		loading.value = false
	}
}
watch(tab, load)
onMounted(load)
const off = onRealtime('runway_notification', load)
onBeforeUnmount(off)

async function open(n: Notification) {
	if (!n.read_at) {
		await api.markRead([n.name])
		n.read_at = dayjs().format()
		ws.setUnread(Math.max(0, (ws.boot.value?.unread_count ?? 1) - 1))
	}
	if (n.work_item) router.push({ query: { peek: n.work_item } })
}

async function toggleRead(n: Notification) {
	await api.markRead([n.name], n.read_at ? 1 : 0)
	load()
}

async function archive(n: Notification) {
	await api.archiveNotification([n.name], n.archived_at ? 1 : 0)
	load()
}

function snoozeOptions(n: Notification) {
	const at = (d: ReturnType<typeof dayjs>) => async () => {
		await api.snoozeNotification([n.name], d.format('YYYY-MM-DD HH:mm:ss'))
		load()
	}
	return [
		{ label: 'In 1 hour', onClick: at(dayjs().add(1, 'hour')) },
		{ label: 'Tomorrow morning', onClick: at(dayjs().add(1, 'day').hour(9).minute(0)) },
		{ label: 'Next week', onClick: at(dayjs().add(1, 'week').day(1).hour(9).minute(0)) },
		{
			label: 'Unsnooze',
			condition: () => !!n.snoozed_until,
			onClick: async () => {
				await api.snoozeNotification([n.name], null)
				load()
			},
		},
	]
}

async function markAll() {
	await api.markAllRead()
	load()
}
</script>
