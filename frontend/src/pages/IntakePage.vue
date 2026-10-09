<template>
	<AppHeader
		:crumbs="[
			{
				label: projectDoc?.title ?? project,
				route: { name: 'ProjectItems', params: { project } },
			},
			{ label: 'Intake' },
		]"
	>
		<template #actions>
			<ProjectTabs :project="project" />
			<Button
				variant="solid"
				icon-left="lucide-plus"
				label="New request"
				@click="submitOpen = true"
			/>
		</template>
	</AppHeader>
	<div class="flex min-h-0 flex-1">
		<div class="flex w-96 shrink-0 flex-col border-r border-outline-gray-1">
			<div class="border-b border-outline-gray-1 p-2">
				<TabButtons v-model="status" size="sm" :options="statusOptions" />
			</div>
			<div class="flex-1 overflow-y-auto">
				<button
					v-for="r in rows"
					:key="r.name"
					type="button"
					class="flex w-full flex-col gap-1 border-b border-outline-gray-1 px-4 py-3 text-left hover:bg-surface-gray-1"
					:class="{ 'bg-surface-gray-2': selected?.name === r.name }"
					@click="selected = r"
				>
					<div class="flex items-center gap-2">
						<span class="text-xs text-ink-gray-5">{{ r.work_item }}</span>
						<Badge
							size="sm"
							:label="r.snoozed ? 'Snoozed' : r.status"
							:theme="THEME[r.status] ?? 'gray'"
						/>
						<span class="ml-auto text-xs text-ink-gray-4">{{
							dayjs(r.creation).fromNow()
						}}</span>
					</div>
					<div class="truncate text-sm font-medium text-ink-gray-8">
						{{ r.item?.title }}
					</div>
					<div class="flex items-center gap-1.5 text-xs text-ink-gray-5">
						<UserAvatar :user="r.submitted_by" size="xs" :tooltip="false" />{{
							ws.userName(r.submitted_by)
						}}
					</div>
				</button>
				<EmptyState
					v-if="!rows.length"
					icon="lucide-inbox"
					title="Intake is clear"
					description="New requests from your team and stakeholders land here for triage."
				/>
			</div>
		</div>
		<div class="min-w-0 flex-1 overflow-y-auto">
			<template v-if="selected">
				<div
					v-if="
						canTriage &&
						(selected.status === 'Pending' || selected.status === 'Snoozed')
					"
					class="flex items-center gap-2 border-b border-outline-gray-1 px-6 py-2"
				>
					<Button
						variant="solid"
						theme="green"
						icon-left="lucide-check"
						label="Accept"
						@click="
							act(
								() => api.acceptIntake(selected!.name),
								'Accepted · moved to backlog',
							)
						"
					/>
					<Button
						theme="red"
						icon-left="lucide-x"
						label="Decline"
						@click="act(() => api.declineIntake(selected!.name), 'Declined')"
					/>
					<Dropdown :options="snoozeOptions">
						<template #default
							><Button icon-left="lucide-alarm-clock" label="Snooze"
						/></template>
					</Dropdown>
					<ItemSearch
						label="Mark duplicate"
						icon="lucide-copy"
						:project="project"
						:exclude="[selected.work_item]"
						@select="
							(i) =>
								act(
									() => api.duplicateIntake(selected!.name, i.name),
									`Marked duplicate of ${i.name}`,
								)
						"
					/>
				</div>
				<WorkItemDetail
					:key="selected.work_item + version"
					:name="selected.work_item"
					layout="page"
				/>
			</template>
			<EmptyState
				v-else
				icon="lucide-mouse-pointer-click"
				title="Select a request"
				description="Pick a request to review, accept, decline, snooze or mark as duplicate."
			/>
		</div>
	</div>

	<Dialog v-model:open="submitOpen" title="Submit a request" size="lg">
		<template #default>
			<div class="space-y-3">
				<FormControl v-model="form.title" label="Title" placeholder="What do you need?" />
				<div>
					<FormLabel label="Details" />
					<RichEditor
						v-model="form.description"
						class="mt-1.5"
						kit="rich"
						placeholder="Context, links, screenshots…"
					/>
				</div>
				<FormControl
					v-model="form.priority"
					type="select"
					label="Priority"
					:options="PRIORITIES"
				/>
			</div>
		</template>
		<template #actions>
			<div class="flex justify-end gap-2">
				<Button label="Cancel" @click="submitOpen = false" />
				<Button
					variant="solid"
					label="Submit"
					:disabled="!form.title"
					:loading="saving"
					@click="submit"
				/>
			</div>
		</template>
	</Dialog>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import {
	Badge,
	Button,
	Dialog,
	Dropdown,
	FormControl,
	FormLabel,
	TabButtons,
	dayjs,
	toast,
} from 'frappe-ui'
import AppHeader from '@/components/common/AppHeader.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ProjectTabs from '@/components/common/ProjectTabs.vue'
import RichEditor from '@/components/common/RichEditor.vue'
import UserAvatar from '@/components/common/UserAvatar.vue'
import ItemSearch from '@/components/workitem/ItemSearch.vue'
import WorkItemDetail from '@/components/workitem/WorkItemDetail.vue'
import { api, errorMessage } from '@/api'
import { useWorkspace } from '@/stores/workspace'
import { PRIORITIES } from '@/utils/constants'

type IntakeRow = Awaited<ReturnType<typeof api.intake>>[number]

const props = defineProps<{ project: string }>()
const ws = useWorkspace()
const projectDoc = computed(() => ws.project(props.project))
const canTriage = computed(
	() => projectDoc.value?.role === 'Admin' || projectDoc.value?.role === 'Member',
)

const THEME: Record<string, 'gray' | 'green' | 'red' | 'amber' | 'blue'> = {
	Pending: 'amber',
	Snoozed: 'gray',
	Accepted: 'green',
	Declined: 'red',
	Duplicate: 'blue',
}
const statusOptions = [
	{ value: 'Pending', label: 'Open' },
	{ value: 'Closed', label: 'Closed' },
]
const status = ref('Pending')
const rows = ref<IntakeRow[]>([])
const selected = ref<IntakeRow | null>(null)
const version = ref(0)
const submitOpen = ref(false)
const saving = ref(false)
const form = reactive({ title: '', description: '', priority: 'None' })

async function load() {
	rows.value = await api.intake(props.project, status.value)
	selected.value =
		rows.value.find((r) => r.name === selected.value?.name) ?? rows.value[0] ?? null
}
watch(status, load)
onMounted(load)

async function act(fn: () => Promise<unknown>, message: string) {
	try {
		await fn()
		toast.success(message)
		version.value++
		await load()
	} catch (e) {
		toast.error(errorMessage(e))
	}
}

const snoozeOptions = computed(() => {
	const snooze = (days: number) => () =>
		act(
			() =>
				api.snoozeIntake(
					selected.value!.name,
					dayjs().add(days, 'day').format('YYYY-MM-DD'),
				),
			`Snoozed for ${days} days`,
		)
	return [
		{ label: '1 day', onClick: snooze(1) },
		{ label: '3 days', onClick: snooze(3) },
		{ label: '1 week', onClick: snooze(7) },
		{
			label: 'Unsnooze',
			onClick: () => act(() => api.snoozeIntake(selected.value!.name, null), 'Unsnoozed'),
		},
	]
})

async function submit() {
	saving.value = true
	try {
		await api.submitIntake(props.project, form.title, form.description, form.priority)
		Object.assign(form, { title: '', description: '', priority: 'None' })
		submitOpen.value = false
		toast.success('Request submitted')
		status.value = 'Pending'
		await load()
	} catch (e) {
		toast.error(errorMessage(e))
	} finally {
		saving.value = false
	}
}
</script>
