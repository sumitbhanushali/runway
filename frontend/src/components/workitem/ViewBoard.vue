<template>
	<WorkItemsBoard :state="state" :project="project" :my-work="myWork">
		<template v-if="doc" #toolbar>
			<Button v-if="dirty" size="sm" label="Reset" @click="reset" />
			<Button
				v-if="canEdit && dirty"
				size="sm"
				icon-left="lucide-save"
				label="Update view"
				@click="saveOpen = true"
			/>
		</template>
	</WorkItemsBoard>
	<SaveViewDialog
		v-if="doc"
		v-model:open="saveOpen"
		:project="project"
		:state="state"
		:view="doc"
		@saved="(d) => emit('saved', d)"
	/>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { Button } from 'frappe-ui'
import SaveViewDialog from '@/components/filters/SaveViewDialog.vue'
import WorkItemsBoard from './WorkItemsBoard.vue'
import { defaultDisplay, useDisplay, type DisplayState } from '@/composables/useDisplay'
import { useWorkspace } from '@/stores/workspace'
import type { SavedView } from '@/types'

const props = defineProps<{
	storageKey: string
	doc?: SavedView
	project?: string
	myWork?: string
}>()
const emit = defineEmits<{ saved: [doc: SavedView] }>()

const ws = useWorkspace()
const saveOpen = ref(false)

function parse<T>(raw: string | null | undefined, fallback: T): T {
	try {
		return raw ? (JSON.parse(raw) as T) : fallback
	} catch {
		return fallback
	}
}

function fromDoc(): DisplayState {
	const base = defaultDisplay()
	if (!props.doc) return base
	return {
		filters: parse(props.doc.filters, {}),
		display: { ...base.display, ...parse(props.doc.display_filters, {}) },
		properties: parse(props.doc.display_properties, base.properties),
	}
}

const saved = fromDoc()
const state = useDisplay(props.storageKey, saved)
const canEdit = computed(() => props.doc?.owner === ws.user.value?.name)
const dirty = computed(() => {
	if (!props.doc) return false
	const { search: _s, ...filters } = state.filters
	void _s
	return (
		JSON.stringify(filters) !== JSON.stringify(saved.filters) ||
		JSON.stringify(state.display) !== JSON.stringify(saved.display) ||
		JSON.stringify(state.properties) !== JSON.stringify(saved.properties)
	)
})

function reset() {
	Object.assign(state, JSON.parse(JSON.stringify(saved)))
}
</script>
