<template>
	<section class="space-y-3">
		<div>
			<div class="mb-2 flex items-center gap-2">
				<h3 class="text-sm font-medium text-ink-gray-8">Links</h3>
				<Button
					v-if="editable && !adding"
					class="ml-auto"
					size="sm"
					variant="ghost"
					icon-left="lucide-plus"
					label="Add link"
					@click="adding = true"
				/>
			</div>
			<form v-if="adding" class="mb-2 flex items-center gap-2" @submit.prevent="addLink">
				<TextInput v-model="url" size="sm" class="flex-1" placeholder="https://…" />
				<TextInput
					v-model="linkTitle"
					size="sm"
					class="w-40"
					placeholder="Title (optional)"
				/>
				<Button size="sm" type="submit" variant="solid" label="Add" :disabled="!url" />
				<Button size="sm" label="Cancel" @click="adding = false" />
			</form>
			<div
				v-for="l in links"
				:key="l.name"
				class="group flex h-8 items-center gap-2 rounded-3 px-2 hover:bg-surface-gray-1"
			>
				<span class="lucide-link size-3.5 text-ink-gray-5" />
				<a
					:href="l.url"
					target="_blank"
					rel="noopener"
					class="flex-1 truncate text-sm text-ink-gray-8 hover:underline"
				>
					{{ l.title || l.url }}
				</a>
				<span class="text-xs text-ink-gray-4">{{ ws.userName(l.owner) }}</span>
				<button
					v-if="editable"
					type="button"
					class="invisible rounded-2 p-1 text-ink-gray-4 hover:bg-surface-gray-3 group-hover:visible"
					@click="removeLink(l.name)"
				>
					<span class="lucide-x block size-3.5" />
				</button>
			</div>
		</div>
		<div>
			<div class="mb-2 flex items-center gap-2">
				<h3 class="text-sm font-medium text-ink-gray-8">Attachments</h3>
				<label v-if="editable" class="ml-auto">
					<input type="file" class="hidden" multiple @change="onFiles" />
					<span
						class="flex h-7 cursor-pointer items-center gap-1.5 rounded-4 px-2 text-sm text-ink-gray-7 hover:bg-surface-gray-2"
					>
						<span
							:class="
								uploading ? 'lucide-loader-circle animate-spin' : 'lucide-upload'
							"
							class="size-3.5"
						/>
						Upload
					</span>
				</label>
			</div>
			<div class="grid gap-2 sm:grid-cols-2">
				<div
					v-for="f in attachments"
					:key="f.name"
					class="group flex items-center gap-2 rounded-4 border border-outline-gray-1 px-2 py-1.5"
				>
					<span class="lucide-file size-4 text-ink-gray-5" />
					<a :href="f.file_url" target="_blank" class="min-w-0 flex-1">
						<div class="truncate text-sm text-ink-gray-8">{{ f.file_name }}</div>
						<div class="text-xs text-ink-gray-4">{{ size(f.file_size) }}</div>
					</a>
					<button
						v-if="editable"
						type="button"
						class="invisible rounded-2 p-1 text-ink-gray-4 hover:bg-surface-gray-3 group-hover:visible"
						@click="removeFile(f.name)"
					>
						<span class="lucide-trash-2 block size-3.5" />
					</button>
				</div>
			</div>
		</div>
	</section>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Button, TextInput, toast, upload } from 'frappe-ui'
import { api, errorMessage } from '@/api'
import { useWorkspace } from '@/stores/workspace'
import type { WorkItemDetail } from '@/types'

const props = defineProps<{
	item: string
	links: WorkItemDetail['links']
	attachments: WorkItemDetail['attachments']
	editable: boolean
}>()
const emit = defineEmits<{ changed: [] }>()

const ws = useWorkspace()
const adding = ref(false)
const url = ref('')
const linkTitle = ref('')
const uploading = ref(false)

async function addLink() {
	try {
		await api.addLink(props.item, url.value, linkTitle.value || undefined)
		url.value = ''
		linkTitle.value = ''
		adding.value = false
		emit('changed')
	} catch (e) {
		toast.error(errorMessage(e))
	}
}

async function removeLink(name: string) {
	await api.removeLink(name)
	emit('changed')
}

async function onFiles(e: Event) {
	const input = e.target as HTMLInputElement
	const files = Array.from(input.files ?? [])
	if (!files.length) return
	uploading.value = true
	try {
		for (const file of files)
			await upload(file, { doctype: 'Runway Work Item', docname: props.item, private: true })
		emit('changed')
	} catch (err) {
		toast.error(errorMessage(err))
	} finally {
		uploading.value = false
		input.value = ''
	}
}

async function removeFile(name: string) {
	await api.removeAttachment(name)
	emit('changed')
}

function size(bytes: number) {
	if (!bytes) return ''
	if (bytes < 1024) return `${bytes} B`
	if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
	return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}
</script>
