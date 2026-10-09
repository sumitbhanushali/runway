<template>
	<AppHeader :crumbs="[{ label: 'Workspace settings', icon: 'lucide-settings' }]" />
	<div class="flex-1 overflow-y-auto p-8">
		<div class="max-w-2xl space-y-8">
			<section class="space-y-3">
				<h2 class="text-base font-medium text-ink-gray-9">General</h2>
				<FormControl v-model="title" label="Name" :disabled="!isAdmin" />
				<FormControl :model-value="ws.workspace.value ?? ''" label="URL" disabled>
					<template #prefix
						><span class="text-sm text-ink-gray-5">/runway/</span></template
					>
				</FormControl>
				<Button v-if="isAdmin" variant="solid" label="Save" @click="saveTitle" />
			</section>

			<section class="space-y-3">
				<h2 class="text-base font-medium text-ink-gray-9">Members</h2>
				<div v-if="isAdmin" class="flex items-end gap-2">
					<FormControl
						v-model="email"
						class="flex-1"
						label="Invite by email"
						placeholder="teammate@company.com"
						type="email"
					/>
					<div class="w-32 shrink-0">
						<FormControl
							v-model="role"
							type="select"
							label="Role"
							:options="['Admin', 'Member', 'Guest']"
						/>
					</div>
					<Button
						variant="solid"
						label="Invite"
						:loading="inviting"
						:disabled="!email"
						@click="invite"
					/>
				</div>
				<div class="overflow-hidden rounded-5 border border-outline-gray-1">
					<div
						v-for="m in ws.members.value"
						:key="m.user"
						class="flex items-center gap-3 border-b border-outline-gray-1 px-4 py-2.5 last:border-b-0"
					>
						<UserAvatar :user="m.user" />
						<div class="flex-1">
							<div class="text-sm text-ink-gray-9">{{ m.full_name }}</div>
							<div class="text-xs text-ink-gray-5">{{ m.email || m.user }}</div>
						</div>
						<template v-if="isAdmin">
							<Select
								:model-value="m.role"
								size="sm"
								class="w-28"
								:options="['Admin', 'Member', 'Guest']"
								@update:model-value="(r) => update(m.user, String(r))"
							/>
							<Button
								size="sm"
								variant="ghost"
								icon="lucide-user-minus"
								@click="remove(m.user)"
							/>
						</template>
						<Badge v-else size="sm" :label="m.role" />
					</div>
				</div>
			</section>
		</div>
	</div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { Badge, Button, FormControl, Select, dialog, toast } from 'frappe-ui'
import AppHeader from '@/components/common/AppHeader.vue'
import UserAvatar from '@/components/common/UserAvatar.vue'
import { api, errorMessage } from '@/api'
import { loadBoot, useWorkspace } from '@/stores/workspace'

const ws = useWorkspace()
const isAdmin = computed(() => ws.workspaceDoc.value?.role === 'Admin')
const title = ref(ws.workspaceDoc.value?.title ?? '')
const email = ref('')
const role = ref('Member')
const inviting = ref(false)

async function refresh() {
	await loadBoot(ws.workspace.value, true)
}

async function saveTitle() {
	try {
		await api.setValue('Runway Workspace', ws.workspace.value!, { title: title.value })
		await refresh()
		toast.success('Saved')
	} catch (e) {
		toast.error(errorMessage(e))
	}
}

async function invite() {
	inviting.value = true
	try {
		await api.inviteMember(ws.workspace.value!, email.value, role.value)
		email.value = ''
		await refresh()
		toast.success('Invitation sent')
	} catch (e) {
		toast.error(errorMessage(e))
	} finally {
		inviting.value = false
	}
}

async function update(user: string, r: string) {
	try {
		await api.updateWorkspaceMember(ws.workspace.value!, user, r)
		await refresh()
	} catch (e) {
		toast.error(errorMessage(e))
	}
}

function remove(user: string) {
	dialog.danger({
		title: `Remove ${ws.userName(user)}?`,
		message: 'They lose access to this workspace and its projects.',
		confirmLabel: 'Remove',
		onConfirm: async ({ close }) => {
			try {
				await api.updateWorkspaceMember(ws.workspace.value!, user, undefined, true)
				await refresh()
			} catch (e) {
				toast.error(errorMessage(e))
			}
			close()
		},
	})
}
</script>
