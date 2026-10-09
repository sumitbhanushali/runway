<template>
	<nav
		class="flex h-full w-60 shrink-0 flex-col border-r border-outline-gray-1 bg-surface-sidebar"
	>
		<div class="p-2">
			<Dropdown :options="workspaceMenu" class="w-full">
				<template #default>
					<button
						type="button"
						class="flex w-full items-center gap-2 rounded-4 px-2 py-1.5 hover:bg-surface-gray-3"
					>
						<span
							class="flex size-6 items-center justify-center rounded-3 bg-surface-gray-7 text-xs font-semibold text-ink-base"
						>
							{{ (ws.workspaceDoc.value?.title || 'R').slice(0, 1) }}
						</span>
						<span class="flex-1 truncate text-left text-sm font-medium text-ink-gray-9">
							{{ ws.workspaceDoc.value?.title || 'Runway' }}
						</span>
						<span class="lucide-chevrons-up-down size-3.5 text-ink-gray-5" />
					</button>
				</template>
			</Dropdown>
		</div>
		<div class="flex items-center gap-1 px-2 pb-2">
			<Button
				class="flex-1"
				icon-left="lucide-square-pen"
				label="New work item"
				@click="bus.emit('create-item', { project: currentProject })"
			/>
			<Button icon="lucide-search" tooltip="Search (⌘K)" @click="emit('search')" />
		</div>
		<div class="flex-1 overflow-y-auto px-2 pb-2">
			<SidebarLink :to="{ name: 'Home' }" icon="lucide-house" label="Home" exact />
			<SidebarLink
				:to="{ name: 'Inbox' }"
				icon="lucide-inbox"
				label="Inbox"
				:badge="ws.boot.value?.unread_count || undefined"
			/>
			<SidebarLink :to="{ name: 'MyWork' }" icon="lucide-user-check" label="Your work" />
			<SidebarLink :to="{ name: 'WorkspaceViews' }" icon="lucide-layers" label="Views" />
			<SidebarLink :to="{ name: 'Analytics' }" icon="lucide-chart-column" label="Analytics" />
			<SidebarLink
				:to="{ name: 'Projects' }"
				icon="lucide-briefcase"
				label="Projects"
				exact
			/>

			<template v-if="favorites.length">
				<div class="mb-1 mt-4 px-2 text-xs font-medium text-ink-gray-5">Favorites</div>
				<SidebarLink
					v-for="f in favorites"
					:key="f.name"
					:to="{ name: 'ProjectItems', params: { project: f.name } }"
					:emoji="f.emoji || undefined"
					icon="lucide-folder"
					:label="f.title"
				/>
			</template>

			<div class="mb-1 mt-4 flex items-center px-2 text-xs font-medium text-ink-gray-5">
				Projects
				<button
					type="button"
					class="ml-auto rounded-2 p-0.5 hover:bg-surface-gray-3"
					@click="router.push({ name: 'Projects', query: { create: '1' } })"
				>
					<span class="lucide-plus block size-3.5" />
				</button>
			</div>
			<div v-for="p in ws.projects.value" :key="p.name">
				<button
					type="button"
					class="flex w-full items-center gap-2 rounded-4 px-2 py-1.5 text-sm text-ink-gray-7 hover:bg-surface-gray-3"
					@click="expanded[p.name] = !isExpanded(p.name)"
				>
					<ProjectIcon :project="p" :size="18" />
					<span class="flex-1 truncate text-left">{{ p.title }}</span>
					<span
						:class="isExpanded(p.name) ? 'lucide-chevron-down' : 'lucide-chevron-right'"
						class="size-3.5 text-ink-gray-4"
					/>
				</button>
				<div v-if="isExpanded(p.name)" class="ml-4 border-l border-outline-gray-2 pl-2">
					<SidebarLink
						:to="{ name: 'ProjectItems', params: { project: p.name } }"
						icon="lucide-layers-2"
						label="Work items"
						small
					/>
					<SidebarLink
						v-if="p.cycles_enabled"
						:to="{ name: 'Cycles', params: { project: p.name } }"
						icon="lucide-refresh-ccw"
						label="Cycles"
						small
					/>
					<SidebarLink
						v-if="p.modules_enabled"
						:to="{ name: 'Modules', params: { project: p.name } }"
						icon="lucide-boxes"
						label="Modules"
						small
					/>
					<SidebarLink
						v-if="p.views_enabled"
						:to="{ name: 'ProjectViews', params: { project: p.name } }"
						icon="lucide-layers"
						label="Views"
						small
					/>
					<SidebarLink
						v-if="p.intake_enabled"
						:to="{ name: 'Intake', params: { project: p.name } }"
						icon="lucide-inbox"
						label="Intake"
						small
					/>
					<SidebarLink
						v-if="p.role === 'Admin'"
						:to="{ name: 'ProjectSettings', params: { project: p.name } }"
						icon="lucide-settings"
						label="Settings"
						small
					/>
				</div>
			</div>
		</div>
		<div class="border-t border-outline-gray-1 p-2">
			<Dropdown :options="userMenu" class="w-full">
				<template #default>
					<button
						type="button"
						class="flex w-full items-center gap-2 rounded-4 px-2 py-1.5 hover:bg-surface-gray-3"
					>
						<UserAvatar
							v-if="ws.user.value"
							:user="ws.user.value.name"
							size="sm"
							:tooltip="false"
						/>
						<span class="flex-1 truncate text-left text-sm text-ink-gray-8">{{
							ws.user.value?.full_name
						}}</span>
					</button>
				</template>
			</Dropdown>
		</div>
	</nav>
</template>

<script setup lang="ts">
import { computed, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Button, Dropdown, useColorScheme } from 'frappe-ui'
import ProjectIcon from '@/components/common/ProjectIcon.vue'
import UserAvatar from '@/components/common/UserAvatar.vue'
import SidebarLink from './SidebarLink.vue'
import { useWorkspace } from '@/stores/workspace'
import { bus } from '@/utils/bus'

const emit = defineEmits<{ search: [] }>()
const ws = useWorkspace()
const route = useRoute()
const router = useRouter()
const expanded = reactive<Record<string, boolean>>({})
const { colorScheme, setColorScheme } = useColorScheme()

const currentProject = computed(() => (route.params.project as string) || undefined)

function isExpanded(name: string) {
	return expanded[name] ?? name === currentProject.value
}

const favorites = computed(() =>
	(ws.boot.value?.favorites ?? [])
		.filter((f) => f.reference_doctype === 'Runway Project')
		.map((f) => ws.project(f.reference_name))
		.filter((p): p is NonNullable<typeof p> => !!p),
)

const workspaceMenu = computed(() => [
	{
		group: 'Workspaces',
		options: (ws.boot.value?.workspaces ?? []).map((w) => ({
			label: w.title,
			icon: w.name === ws.workspace.value ? 'lucide-check' : null,
			onClick: () => router.push({ name: 'Home', params: { workspace: w.name } }),
		})),
	},
	{
		group: 'Actions',
		hideLabel: true,
		options: [
			{
				label: 'Workspace settings',
				icon: 'lucide-settings',
				onClick: () => router.push({ name: 'WorkspaceSettings' }),
			},
			{
				label: 'Create workspace',
				icon: 'lucide-plus',
				onClick: () => router.push({ name: 'Onboarding' }),
			},
		],
	},
])

const userMenu = computed(() => [
	{
		label: 'Theme',
		icon: 'lucide-sun-moon',
		submenu: (['light', 'dark', 'system'] as const).map((s) => ({
			label: s[0].toUpperCase() + s.slice(1),
			icon: colorScheme.value === s ? 'lucide-check' : null,
			onClick: () => setColorScheme(s),
		})),
	},
	{
		label: 'Open Desk',
		icon: 'lucide-app-window',
		condition: () => !!window.is_system_manager,
		onClick: () => {
			window.location.href = '/app'
		},
	},
	{
		label: 'Log out',
		icon: 'lucide-log-out',
		onClick: () => {
			window.location.href = '/?cmd=web_logout'
		},
	},
])
</script>
