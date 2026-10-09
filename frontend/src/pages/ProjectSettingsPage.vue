<template>
	<AppHeader
		:crumbs="[
			{ label: p?.title ?? project, route: { name: 'ProjectItems', params: { project } } },
			{ label: 'Settings' },
		]"
	>
		<template #actions><ProjectTabs :project="project" /></template>
	</AppHeader>
	<div v-if="p" class="flex min-h-0 flex-1">
		<nav class="w-52 shrink-0 space-y-0.5 border-r border-outline-gray-1 p-3">
			<router-link
				v-for="t in TABS"
				:key="t.value"
				:to="{ name: 'ProjectSettings', params: { project, tab: t.value } }"
				class="flex items-center gap-2 rounded-4 px-2 py-1.5 text-sm"
				:class="
					current === t.value
						? 'bg-surface-gray-2 font-medium text-ink-gray-9'
						: 'text-ink-gray-6 hover:bg-surface-gray-1'
				"
			>
				<span :class="t.icon" class="size-4" /> {{ t.label }}
			</router-link>
		</nav>
		<div class="flex-1 overflow-y-auto p-8">
			<div class="max-w-2xl space-y-6">
				<!-- General -->
				<template v-if="current === 'general'">
					<div class="flex gap-3">
						<div class="w-20 shrink-0">
							<FormControl v-model="general.emoji" label="Icon" />
						</div>
						<FormControl v-model="general.title" class="flex-1" label="Name" />
					</div>
					<FormControl
						:model-value="p.identifier"
						label="Identifier"
						disabled
						description="Identifiers cannot change once work items are numbered."
					/>
					<FormControl
						v-model="general.description"
						type="textarea"
						label="Description"
					/>
					<div class="grid grid-cols-2 gap-3">
						<FormControl
							v-model="general.network"
							type="select"
							label="Access"
							:options="['Public', 'Secret']"
						/>
						<FormControl
							v-model="general.lead"
							type="select"
							label="Lead"
							:options="[{ label: 'None', value: '' }, ...memberOptions]"
						/>
						<FormControl
							v-model="general.default_assignee"
							type="select"
							label="Default assignee"
							:options="[{ label: 'None', value: '' }, ...memberOptions]"
						/>
					</div>
					<div class="flex gap-2">
						<Button
							variant="solid"
							label="Save"
							:loading="saving"
							@click="saveGeneral"
						/>
						<Button
							:label="p.archived ? 'Restore project' : 'Archive project'"
							@click="save({ archived: p.archived ? 0 : 1 })"
						/>
					</div>
				</template>

				<!-- Features -->
				<template v-else-if="current === 'features'">
					<div
						v-for="f in FEATURES"
						:key="f.key"
						class="flex items-center justify-between rounded-5 border border-outline-gray-1 p-4"
					>
						<div>
							<div class="flex items-center gap-2 font-medium text-ink-gray-9">
								<span :class="f.icon" class="size-4" />{{ f.label }}
							</div>
							<p class="mt-0.5 text-sm text-ink-gray-5">{{ f.description }}</p>
						</div>
						<Switch
							:model-value="!!p[f.key]"
							@update:model-value="(v: boolean) => save({ [f.key]: v ? 1 : 0 })"
						/>
					</div>
				</template>

				<!-- Members -->
				<template v-else-if="current === 'members'">
					<div class="flex items-end gap-2">
						<FormControl
							v-model="newMember"
							type="select"
							class="flex-1"
							label="Add member"
							:options="addableMembers"
						/>
						<div class="w-32 shrink-0">
							<FormControl
								v-model="newRole"
								type="select"
								label="Role"
								:options="['Admin', 'Member', 'Guest']"
							/>
						</div>
						<Button
							variant="solid"
							label="Add"
							:disabled="!newMember"
							@click="addMember"
						/>
					</div>
					<div class="overflow-hidden rounded-5 border border-outline-gray-1">
						<div
							v-for="m in p.members"
							:key="m.user"
							class="flex items-center gap-3 border-b border-outline-gray-1 px-4 py-2.5 last:border-b-0"
						>
							<UserAvatar :user="m.user" />
							<div class="flex-1">
								<div class="text-sm text-ink-gray-9">{{ m.full_name }}</div>
								<div class="text-xs text-ink-gray-5">{{ m.user }}</div>
							</div>
							<Select
								:model-value="m.role"
								class="w-28"
								size="sm"
								:options="['Admin', 'Member', 'Guest']"
								@update:model-value="(r) => setRole(m.user, String(r))"
							/>
							<Button
								size="sm"
								variant="ghost"
								icon="lucide-user-minus"
								@click="removeMember(m.user)"
							/>
						</div>
					</div>
				</template>

				<!-- States -->
				<template v-else-if="current === 'states'">
					<p class="text-sm text-ink-gray-5">
						Every state belongs to a group. Reports and progress use the group, so
						rename freely.
					</p>
					<div
						v-for="g in STATE_GROUPS"
						:key="g"
						class="rounded-5 border border-outline-gray-1"
					>
						<div
							class="flex items-center gap-2 border-b border-outline-gray-1 bg-surface-gray-1 px-4 py-2"
						>
							<StateIcon :group="g" /><span
								class="text-sm font-medium text-ink-gray-8"
								>{{ g }}</span
							>
							<Button
								class="ml-auto"
								size="sm"
								variant="ghost"
								icon-left="lucide-plus"
								label="Add"
								@click="addState(g)"
							/>
						</div>
						<div
							v-for="s in p.states.filter((x) => x.state_group === g)"
							:key="s.name"
							class="flex items-center gap-2 border-b border-outline-gray-1 px-4 py-2 last:border-b-0"
						>
							<input
								type="color"
								:value="s.color"
								class="size-6 cursor-pointer rounded-2 border-0 p-0"
								@change="
									(e) =>
										updateDoc('Runway State', s.name, {
											color: (e.target as HTMLInputElement).value,
										})
								"
							/>
							<input
								:value="s.title"
								class="h-7 flex-1 rounded-3 border-0 bg-transparent px-1 text-sm text-ink-gray-9 hover:bg-surface-gray-2 focus:bg-surface-gray-2 focus:ring-0"
								@change="
									(e) =>
										updateDoc('Runway State', s.name, {
											title: (e.target as HTMLInputElement).value,
										})
								"
							/>
							<Badge v-if="s.is_default" size="sm" label="Default" />
							<Button
								v-else
								size="sm"
								variant="ghost"
								label="Make default"
								@click="updateDoc('Runway State', s.name, { is_default: 1 })"
							/>
							<Button
								size="sm"
								variant="ghost"
								icon="lucide-trash-2"
								@click="removeDoc('Runway State', s.name)"
							/>
						</div>
					</div>
				</template>

				<!-- Labels -->
				<template v-else-if="current === 'labels'">
					<div class="flex items-end gap-2">
						<FormControl
							v-model="newLabel"
							class="flex-1"
							label="New label"
							placeholder="e.g. Frontend"
							@keydown.enter="addLabel"
						/>
						<Button
							variant="solid"
							label="Add"
							:disabled="!newLabel"
							@click="addLabel"
						/>
					</div>
					<div class="overflow-hidden rounded-5 border border-outline-gray-1">
						<div
							v-for="l in p.labels"
							:key="l.name"
							class="flex items-center gap-2 border-b border-outline-gray-1 px-4 py-2 last:border-b-0"
						>
							<input
								type="color"
								:value="l.color"
								class="size-6 cursor-pointer rounded-2 border-0 p-0"
								@change="
									(e) =>
										updateDoc('Runway Label', l.name, {
											color: (e.target as HTMLInputElement).value,
										})
								"
							/>
							<input
								:value="l.title"
								class="h-7 flex-1 rounded-3 border-0 bg-transparent px-1 text-sm text-ink-gray-9 hover:bg-surface-gray-2 focus:bg-surface-gray-2 focus:ring-0"
								@change="
									(e) =>
										updateDoc('Runway Label', l.name, {
											title: (e.target as HTMLInputElement).value,
										})
								"
							/>
							<Button
								size="sm"
								variant="ghost"
								icon="lucide-trash-2"
								@click="removeDoc('Runway Label', l.name)"
							/>
						</div>
					</div>
				</template>

				<!-- Estimates -->
				<template v-else-if="current === 'estimates'">
					<p class="text-sm text-ink-gray-5">
						Estimates feed cycle burndowns and module progress. Leave empty to turn
						estimates off.
					</p>
					<FormControl
						v-model="estimateType"
						type="select"
						label="Type"
						:options="['Points', 'Categories']"
					/>
					<div class="flex flex-wrap gap-2">
						<Button
							v-for="preset in PRESETS[estimateType]"
							:key="preset.label"
							size="sm"
							:label="preset.label"
							@click="estimatePoints = preset.values.join(', ')"
						/>
					</div>
					<FormControl
						v-model="estimatePoints"
						label="Values (comma separated, smallest first)"
						placeholder="1, 2, 3, 5, 8"
					/>
					<Button variant="solid" label="Save estimates" @click="saveEstimate" />
				</template>
			</div>
		</div>
	</div>
	<EmptyState v-else icon="lucide-lock" title="Project not found" />
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { Badge, Button, FormControl, Select, Switch, dialog, toast } from 'frappe-ui'
import AppHeader from '@/components/common/AppHeader.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ProjectTabs from '@/components/common/ProjectTabs.vue'
import StateIcon from '@/components/common/StateIcon.vue'
import UserAvatar from '@/components/common/UserAvatar.vue'
import { api, errorMessage } from '@/api'
import { refreshProject, upsertProject, useWorkspace } from '@/stores/workspace'
import type { Project, StateGroup } from '@/types'
import { STATE_GROUPS } from '@/utils/constants'

const props = defineProps<{ project: string; tab?: string }>()
const ws = useWorkspace()
const p = computed(() => ws.project(props.project))
const current = computed(() => props.tab || 'general')

const TABS = [
	{ value: 'general', label: 'General', icon: 'lucide-settings' },
	{ value: 'members', label: 'Members', icon: 'lucide-users' },
	{ value: 'features', label: 'Features', icon: 'lucide-toggle-right' },
	{ value: 'states', label: 'States', icon: 'lucide-circle-dot' },
	{ value: 'labels', label: 'Labels', icon: 'lucide-tag' },
	{ value: 'estimates', label: 'Estimates', icon: 'lucide-triangle' },
]
const FEATURES = [
	{
		key: 'cycles_enabled',
		label: 'Cycles',
		icon: 'lucide-refresh-ccw',
		description: 'Time-boxed iterations with burndown charts.',
	},
	{
		key: 'modules_enabled',
		label: 'Modules',
		icon: 'lucide-boxes',
		description: 'Group work by feature or epic across cycles.',
	},
	{
		key: 'views_enabled',
		label: 'Views',
		icon: 'lucide-layers',
		description: 'Save filtered layouts for the team or yourself.',
	},
	{
		key: 'intake_enabled',
		label: 'Intake',
		icon: 'lucide-inbox',
		description: 'A triage queue for requests from members and guests.',
	},
] as const
const PRESETS: Record<string, { label: string; values: string[] }[]> = {
	Points: [
		{ label: 'Fibonacci', values: ['1', '2', '3', '5', '8', '13'] },
		{ label: 'Linear', values: ['1', '2', '3', '4', '5'] },
		{ label: 'Squares', values: ['1', '4', '9', '16', '25'] },
	],
	Categories: [{ label: 'T-shirt', values: ['XS', 'S', 'M', 'L', 'XL'] }],
}

const general = reactive({
	title: '',
	emoji: '',
	description: '',
	network: 'Public',
	lead: '',
	default_assignee: '',
})
const estimateType = ref('Points')
const estimatePoints = ref('')
watch(
	p,
	(x) => {
		if (!x) return
		Object.assign(general, {
			title: x.title,
			emoji: x.emoji ?? '',
			description: (x.description ?? '').replace(/<[^>]+>/g, ''),
			network: x.network,
			lead: x.lead ?? '',
			default_assignee: x.default_assignee ?? '',
		})
		estimateType.value = x.estimate_type ?? 'Points'
		estimatePoints.value = x.estimate_points.join(', ')
	},
	{ immediate: true },
)

const saving = ref(false)
const memberOptions = computed(() =>
	(p.value?.members ?? []).map((m) => ({ label: m.full_name || m.user, value: m.user })),
)
const addableMembers = computed(() =>
	ws.members.value
		.filter((m) => !p.value?.members.some((x) => x.user === m.user))
		.map((m) => ({ label: m.full_name || m.user, value: m.user })),
)
const newMember = ref('')
const newRole = ref('Member')
const newLabel = ref('')

async function run<T>(fn: () => Promise<T>) {
	try {
		const out = await fn()
		await refreshProject(props.project)
		return out
	} catch (e) {
		toast.error(errorMessage(e))
	}
}

async function save(values: Partial<Project>) {
	saving.value = true
	try {
		upsertProject(await api.updateProject(props.project, values))
		toast.success('Saved')
	} catch (e) {
		toast.error(errorMessage(e))
	} finally {
		saving.value = false
	}
}

function saveGeneral() {
	save({
		...general,
		lead: general.lead || null,
		default_assignee: general.default_assignee || null,
	} as Partial<Project>)
}

const addMember = () =>
	run(async () => {
		await api.addProjectMember(props.project, newMember.value, newRole.value)
		newMember.value = ''
	})
const setRole = (user: string, role: string) =>
	run(() => api.addProjectMember(props.project, user, role))
const removeMember = (user: string) => run(() => api.removeProjectMember(props.project, user))

const updateDoc = (doctype: string, name: string, values: Record<string, unknown>) =>
	run(() => api.setValue(doctype, name, values))
function removeDoc(doctype: string, name: string) {
	dialog.danger({
		title: 'Delete?',
		message: 'This cannot be undone.',
		onConfirm: async ({ close }) => {
			await run(() => api.remove(doctype, name))
			close()
		},
	})
}

function addState(group: StateGroup) {
	run(() =>
		api.insert({
			doctype: 'Runway State',
			project: props.project,
			title: `New ${group.toLowerCase()} state`,
			state_group: group,
			color: '#6b7280',
		}),
	)
}

function addLabel() {
	if (!newLabel.value) return
	const palette = ['#ef4444', '#f59e0b', '#10b981', '#3b82f6', '#8b5cf6', '#ec4899', '#14b8a6']
	run(() =>
		api.insert({
			doctype: 'Runway Label',
			project: props.project,
			title: newLabel.value,
			color: palette[(p.value?.labels.length ?? 0) % palette.length],
		}),
	)
	newLabel.value = ''
}

async function saveEstimate() {
	const points = estimatePoints.value
		.split(',')
		.map((s) => s.trim())
		.filter(Boolean)
	try {
		upsertProject(await api.setEstimate(props.project, estimateType.value, points))
		toast.success(points.length ? 'Estimates saved' : 'Estimates turned off')
	} catch (e) {
		toast.error(errorMessage(e))
	}
}
</script>
