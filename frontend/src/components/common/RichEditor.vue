<template>
	<Editor
		v-model="model"
		:extensions="extensions"
		:placeholder="placeholder"
		:editable="editable"
		:autofocus="autofocus"
		:upload-function="uploadFile"
	>
		<template #default="{ editor, isEmpty }">
			<div
				class="flex flex-col rounded-4"
				:class="
					bordered
						? 'border border-outline-gray-2 bg-surface-base focus-within:border-outline-gray-4'
						: ''
				"
				@keydown="onKeydown($event, isEmpty)"
			>
				<EditorContent :editor="editor" :class="contentClass" class="runway-prose" />
				<div
					v-if="editable && toolbar"
					class="flex items-center justify-between gap-2 border-t border-outline-gray-2 px-2 py-1.5"
				>
					<EditorFixedMenu
						:editor="editor"
						:items="kit === 'rich' ? articleToolbar : commentToolbar"
						button-size="xs"
						class="min-w-0 overflow-x-auto"
					/>
					<slot name="actions" :editor="editor" :is-empty="isEmpty" />
				</div>
			</div>
		</template>
	</Editor>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { upload } from 'frappe-ui'
import {
	CommentKit,
	Editor,
	EditorContent,
	EditorFixedMenu,
	RichTextKit,
	articleToolbar,
	commentToolbar,
	type CommentKitOptions,
	type RichTextKitOptions,
	type UploadedFile as EditorUploadedFile,
} from 'frappe-ui/editor'
import { useWorkspace } from '@/stores/workspace'

const props = withDefaults(
	defineProps<{
		kit?: 'comment' | 'rich'
		placeholder?: string
		editable?: boolean
		autofocus?: boolean
		/** Users offered in the @mention menu. Defaults to the workspace's members. */
		mentionUsers?: string[]
		submitOnModEnter?: boolean
		contentClass?: string
		bordered?: boolean
		toolbar?: boolean
	}>(),
	{
		kit: 'comment',
		editable: true,
		autofocus: false,
		submitOnModEnter: false,
		contentClass: 'min-h-20 px-3 py-2',
		bordered: true,
		toolbar: true,
	},
)

const emit = defineEmits<{ submit: [] }>()
const model = defineModel<string>({ default: '' })

defineSlots<{ actions?: (props: { editor: unknown; isEmpty: boolean }) => unknown }>()

const ws = useWorkspace()
const mentions = computed(() => {
	const users = props.mentionUsers ?? ws.members.value.map((m) => m.user)
	return users.map((u) => ({
		id: u,
		label: ws.userName(u),
		image: ws.member(u)?.user_image || undefined,
	}))
})

const extensions = computed(() => {
	const mention: Partial<CommentKitOptions> = { mention: { items: () => mentions.value } }
	if (props.kit === 'rich') return [RichTextKit.configure(mention as Partial<RichTextKitOptions>)]
	return [CommentKit.configure(mention)]
})

async function uploadFile(file: File): Promise<EditorUploadedFile> {
	const uploaded = await upload(file, { private: false })
	return { ...uploaded }
}

function onKeydown(event: KeyboardEvent, isEmpty: boolean) {
	if (!props.submitOnModEnter || event.key !== 'Enter' || !(event.metaKey || event.ctrlKey))
		return
	if (isEmpty) return
	event.preventDefault()
	emit('submit')
}
</script>
