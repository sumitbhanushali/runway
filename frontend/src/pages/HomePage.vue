<template>
	<AppHeader :crumbs="[{ label: 'Home', icon: 'lucide-house' }]" />
	<div class="flex-1 overflow-y-auto">
		<div class="mx-auto max-w-4xl space-y-8 p-6">
			<div>
				<h1 class="text-2xl font-semibold text-ink-gray-9">
					{{ greeting }}, {{ firstName }}
				</h1>
				<p class="mt-1 text-ink-gray-5">{{ dayjs().format('dddd, MMMM D') }}</p>
			</div>

			<div class="grid grid-cols-2 gap-3 sm:grid-cols-4">
				<router-link
					v-for="card in cards"
					:key="card.label"
					:to="card.to"
					class="rounded-5 border border-outline-gray-1 p-4 hover:border-outline-gray-3"
				>
					<div class="text-sm text-ink-gray-5">{{ card.label }}</div>
					<div class="mt-1 text-2xl font-semibold" :class="card.tone">
						{{ card.value ?? '–' }}
					</div>
				</router-link>
			</div>

			<section>
				<h2 class="mb-2 text-base font-medium text-ink-gray-8">Upcoming due dates</h2>
				<div
					v-if="data?.upcoming.length"
					class="overflow-hidden rounded-5 border border-outline-gray-1"
				>
					<button
						v-for="item in data.upcoming"
						:key="item.name"
						type="button"
						class="flex h-10 w-full items-center gap-3 border-b border-outline-gray-1 px-4 text-left last:border-b-0 hover:bg-surface-gray-1"
						@click="peek(item.name)"
					>
						<StateIcon :group="item.state_group" />
						<span class="w-20 text-sm text-ink-gray-5">{{ item.name }}</span>
						<span class="flex-1 truncate text-sm text-ink-gray-8">{{
							item.title
						}}</span>
						<span
							class="text-sm"
							:class="isOverdue(item.due_date) ? 'text-ink-red-4' : 'text-ink-gray-5'"
						>
							{{ dayjs(item.due_date).format('MMM D') }}
						</span>
					</button>
				</div>
				<p v-else class="text-sm text-ink-gray-4">Nothing due. Enjoy the calm.</p>
			</section>

			<section>
				<h2 class="mb-2 text-base font-medium text-ink-gray-8">Recently visited</h2>
				<div v-if="data?.recents.length" class="grid gap-2 sm:grid-cols-2">
					<button
						v-for="r in data.recents"
						:key="r.reference_name"
						type="button"
						class="flex items-center gap-2 rounded-4 border border-outline-gray-1 px-3 py-2 text-left hover:bg-surface-gray-1"
						@click="openRecent(r)"
					>
						<span class="lucide-history size-4 text-ink-gray-4" />
						<span class="w-20 shrink-0 text-sm text-ink-gray-5">{{
							r.reference_name
						}}</span>
						<span class="truncate text-sm text-ink-gray-8">{{ r.title }}</span>
					</button>
				</div>
				<p v-else class="text-sm text-ink-gray-4">Items you open will show up here.</p>
			</section>

			<section
				v-if="!ws.projects.value.length"
				class="rounded-5 border border-dashed border-outline-gray-3 p-6 text-center"
			>
				<p class="mb-3 text-ink-gray-6">
					Create your first project to start tracking work.
				</p>
				<Button
					variant="solid"
					label="Create project"
					:route="{ name: 'Projects', query: { create: '1' } }"
				/>
			</section>
		</div>
	</div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Button, dayjs } from 'frappe-ui'
import AppHeader from '@/components/common/AppHeader.vue'
import StateIcon from '@/components/common/StateIcon.vue'
import { api } from '@/api'
import { useWorkspace } from '@/stores/workspace'

const ws = useWorkspace()
const router = useRouter()
const data = ref<Awaited<ReturnType<typeof api.home>> | null>(null)

const firstName = computed(() => ws.user.value?.full_name?.split(' ')[0] ?? '')
const greeting = computed(() => {
	const h = new Date().getHours()
	return h < 12 ? 'Good morning' : h < 18 ? 'Good afternoon' : 'Good evening'
})
const cards = computed(() => [
	{
		label: 'Assigned to you',
		value: data.value?.counts.open,
		to: { name: 'MyWork', params: { tab: 'assigned' } },
		tone: 'text-ink-gray-9',
	},
	{
		label: 'Overdue',
		value: data.value?.counts.overdue,
		to: { name: 'MyWork', params: { tab: 'assigned' } },
		tone: 'text-ink-red-4',
	},
	{
		label: 'Due this week',
		value: data.value?.counts.due_this_week,
		to: { name: 'MyWork', params: { tab: 'assigned' } },
		tone: 'text-ink-amber-4',
	},
	{
		label: 'Completed',
		value: data.value?.counts.completed,
		to: { name: 'MyWork', params: { tab: 'assigned' } },
		tone: 'text-ink-green-4',
	},
])

onMounted(async () => {
	if (ws.workspace.value) data.value = await api.home(ws.workspace.value)
})

function isOverdue(d: string | null) {
	return !!d && dayjs(d).isBefore(dayjs(), 'day')
}

function peek(name: string) {
	router.push({ query: { peek: name } })
}

function openRecent(r: { reference_doctype: string; reference_name: string }) {
	if (r.reference_doctype === 'Runway Work Item') peek(r.reference_name)
	else if (r.reference_doctype === 'Runway Project')
		router.push({ name: 'ProjectItems', params: { project: r.reference_name } })
}
</script>
