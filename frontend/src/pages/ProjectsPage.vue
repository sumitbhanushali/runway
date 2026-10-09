<template>
	<AppHeader :crumbs="[{ label: 'Projects', icon: 'lucide-briefcase' }]">
		<template #actions>
			<Button
				variant="solid"
				icon-left="lucide-plus"
				label="New project"
				@click="openCreate"
			/>
		</template>
	</AppHeader>
	<div class="flex-1 overflow-y-auto p-6">
		<div class="mx-auto grid max-w-5xl gap-4 sm:grid-cols-2 lg:grid-cols-3">
			<router-link
				v-for="p in ws.projects.value"
				:key="p.name"
				:to="{ name: 'ProjectItems', params: { project: p.name } }"
				class="group flex flex-col gap-3 rounded-5 border border-outline-gray-1 p-4 hover:border-outline-gray-3"
			>
				<div class="flex items-center gap-2">
					<ProjectIcon :project="p" :size="28" />
					<div class="min-w-0 flex-1">
						<div class="truncate font-medium text-ink-gray-9">{{ p.title }}</div>
						<div class="text-xs text-ink-gray-5">
							{{ p.identifier }} · {{ p.network }}
						</div>
					</div>
					<button
						type="button"
						class="rounded-3 p-1 hover:bg-surface-gray-2"
						@click.prevent="ws.toggleFavorite('Runway Project', p.name)"
					>
						<span
							class="block size-4"
							:class="
								ws.isFavorite('Runway Project', p.name)
									? 'lucide-star text-ink-amber-3'
									: 'lucide-star text-ink-gray-4'
							"
						/>
					</button>
				</div>
				<p class="line-clamp-2 min-h-10 text-sm text-ink-gray-6">
					{{ strip(p.description) || 'No description' }}
				</p>
				<div class="flex items-center justify-between">
					<AvatarGroup :users="p.members.map((m) => m.user)" :max="5" />
					<Badge :label="p.role" size="sm" />
				</div>
			</router-link>
		</div>

		<div v-if="ws.boot.value?.joinable_projects.length" class="mx-auto mt-10 max-w-5xl">
			<h2 class="mb-3 text-base font-medium text-ink-gray-8">Other public projects</h2>
			<div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
				<div
					v-for="p in ws.boot.value.joinable_projects"
					:key="p.name"
					class="flex items-center gap-2 rounded-5 border border-dashed border-outline-gray-2 p-3"
				>
					<ProjectIcon :project="p" :size="24" />
					<span class="flex-1 truncate text-sm text-ink-gray-8">{{ p.title }}</span>
					<Button size="sm" label="Join" @click="join(p.name)" />
				</div>
			</div>
		</div>

		<EmptyState
			v-if="!ws.projects.value.length && !ws.boot.value?.joinable_projects.length"
			icon="lucide-briefcase"
			title="No projects yet"
			description="Projects hold work items, cycles, modules and views."
		/>
	</div>

	<Dialog v-model:open="createOpen" title="Create project" size="lg">
		<template #default>
			<form class="space-y-3" @submit.prevent="create">
				<div class="flex gap-2">
					<div class="w-20 shrink-0">
						<FormControl v-model="form.emoji" label="Icon" placeholder="🚀" />
					</div>
					<FormControl
						v-model="form.title"
						class="flex-1"
						label="Name"
						placeholder="Website redesign"
					/>
				</div>
				<FormControl
					v-model="form.identifier"
					label="Identifier"
					description="Prefix for work item IDs, e.g. WEB-12. Up to 12 letters or digits."
				/>
				<FormControl v-model="form.description" type="textarea" label="Description" />
				<FormControl
					v-model="form.network"
					type="select"
					label="Access"
					:options="[
						{ label: 'Public — anyone in the workspace can join', value: 'Public' },
						{ label: 'Secret — invite only', value: 'Secret' },
					]"
				/>
				<ErrorMessage :message="error" />
			</form>
		</template>
		<template #actions>
			<div class="flex justify-end gap-2">
				<Button label="Cancel" @click="createOpen = false" />
				<Button
					variant="solid"
					label="Create project"
					:loading="saving"
					:disabled="!form.title || !form.identifier"
					@click="create"
				/>
			</div>
		</template>
	</Dialog>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Badge, Button, Dialog, ErrorMessage, FormControl, toast } from 'frappe-ui'
import AppHeader from '@/components/common/AppHeader.vue'
import AvatarGroup from '@/components/common/AvatarGroup.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ProjectIcon from '@/components/common/ProjectIcon.vue'
import { api, errorMessage } from '@/api'
import { upsertProject, useWorkspace } from '@/stores/workspace'

const ws = useWorkspace()
const route = useRoute()
const router = useRouter()
const createOpen = ref(false)
const saving = ref(false)
const error = ref('')
const form = reactive({ title: '', identifier: '', description: '', network: 'Public', emoji: '' })
let identifierEdited = false

function deriveIdentifier(title: string) {
	const words = title
		.toUpperCase()
		.replace(/[^A-Z0-9 ]/g, '')
		.split(/\s+/)
		.filter(Boolean)
	if (!words.length) return ''
	const id = words.length > 1 ? words.map((w) => w[0]).join('') : words[0].slice(0, 4)
	return id.replace(/^[0-9]+/, '').slice(0, 12)
}

watch(
	() => form.title,
	(t) => {
		if (!identifierEdited) form.identifier = deriveIdentifier(t)
	},
)
watch(
	() => form.identifier,
	(v) => {
		form.identifier = v
			.toUpperCase()
			.replace(/[^A-Z0-9]/g, '')
			.slice(0, 12)
		if (v !== deriveIdentifier(form.title)) identifierEdited = true
	},
)

function openCreate() {
	Object.assign(form, {
		title: '',
		identifier: '',
		description: '',
		network: 'Public',
		emoji: '',
	})
	identifierEdited = false
	error.value = ''
	createOpen.value = true
}

onMounted(() => {
	if (route.query.create) {
		openCreate()
		router.replace({ query: {} })
	}
})

function strip(html?: string | null) {
	return (html ?? '').replace(/<[^>]+>/g, ' ').trim()
}

async function create() {
	if (!ws.workspace.value) return
	saving.value = true
	error.value = ''
	try {
		const project = await api.createProject({ workspace: ws.workspace.value, ...form })
		upsertProject(project)
		createOpen.value = false
		toast.success(`${project.title} created`)
		router.push({ name: 'ProjectItems', params: { project: project.name } })
	} catch (e) {
		error.value = errorMessage(e)
	} finally {
		saving.value = false
	}
}

async function join(name: string) {
	try {
		upsertProject(await api.joinProject(name))
		toast.success('Joined project')
	} catch (e) {
		toast.error(errorMessage(e))
	}
}
</script>
