<template>
	<Popover v-model:open="open" align="start" :offset="4" bare>
		<template #trigger>
			<slot name="trigger" :open="open" :selected="selectedOptions">
				<button
					type="button"
					:disabled="disabled"
					class="flex h-6 max-w-full items-center gap-1.5 rounded-3 px-1.5 text-sm text-ink-gray-7 transition-colors hover:bg-surface-gray-2 disabled:cursor-default disabled:hover:bg-transparent"
					:class="bordered ? 'border border-outline-gray-2' : ''"
					@click.stop
				>
					<slot name="value" :selected="selectedOptions">
						<template v-if="selectedOptions.length">
							<OptionMark v-if="selectedOptions[0]" :option="selectedOptions[0]" />
							<span class="truncate">
								{{
									selectedOptions.length > 1
										? `${selectedOptions.length} selected`
										: selectedOptions[0].label
								}}
							</span>
						</template>
						<template v-else>
							<span
								v-if="placeholderIcon"
								:class="placeholderIcon"
								class="size-3.5 text-ink-gray-4"
							/>
							<span class="truncate text-ink-gray-4">{{ placeholder }}</span>
						</template>
					</slot>
				</button>
			</slot>
		</template>
		<template #default>
			<div
				class="w-60 rounded-4 bg-surface-elevation-2 p-1 shadow-2xl ring-1 ring-black/5"
				@click.stop
				@keydown.down.prevent="move(1)"
				@keydown.up.prevent="move(-1)"
				@keydown.enter.prevent="pickActive"
			>
				<input
					v-if="searchable"
					ref="searchEl"
					v-model="query"
					class="mb-1 h-7 w-full rounded-3 border-0 bg-surface-gray-2 px-2 text-sm text-ink-gray-8 placeholder-ink-gray-4 focus:ring-0"
					:placeholder="searchPlaceholder"
				/>
				<div class="max-h-64 overflow-y-auto">
					<button
						v-for="(opt, i) in filtered"
						:key="String(opt.value)"
						type="button"
						class="flex w-full items-center gap-2 rounded-3 px-2 py-1.5 text-left text-sm text-ink-gray-8"
						:class="i === active ? 'bg-surface-gray-3' : 'hover:bg-surface-gray-2'"
						@mouseenter="active = i"
						@click="pick(opt)"
					>
						<OptionMark :option="opt" />
						<span class="flex-1 truncate">{{ opt.label }}</span>
						<span
							v-if="isSelected(opt)"
							class="lucide-check size-3.5 text-ink-gray-7"
						/>
					</button>
					<div
						v-if="!filtered.length"
						class="px-2 py-3 text-center text-sm text-ink-gray-4"
					>
						No matches
					</div>
				</div>
				<button
					v-if="clearable && selectedOptions.length"
					type="button"
					class="mt-1 flex w-full items-center gap-2 rounded-3 border-t border-outline-gray-1 px-2 py-1.5 text-sm text-ink-gray-5 hover:bg-surface-gray-2"
					@click="clear"
				>
					<span class="lucide-x size-3.5" /> Clear
				</button>
			</div>
		</template>
	</Popover>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { Popover } from 'frappe-ui'
import OptionMark from './OptionMark.vue'
import type { PickerOption } from './types'

const props = withDefaults(
	defineProps<{
		options: PickerOption[]
		multiple?: boolean
		placeholder?: string
		placeholderIcon?: string
		searchPlaceholder?: string
		searchable?: boolean
		clearable?: boolean
		disabled?: boolean
		bordered?: boolean
	}>(),
	{
		multiple: false,
		placeholder: 'None',
		searchPlaceholder: 'Search…',
		searchable: true,
		clearable: false,
		disabled: false,
		bordered: false,
	},
)

const model = defineModel<string | string[] | null>()
const emit = defineEmits<{ change: [value: string | string[] | null] }>()

const open = ref(false)
const query = ref('')
const active = ref(0)
const searchEl = ref<HTMLInputElement | null>(null)

const values = computed<string[]>(() =>
	Array.isArray(model.value) ? model.value : model.value ? [model.value] : [],
)
const selectedOptions = computed(
	() =>
		values.value
			.map((v) => props.options.find((o) => o.value === v))
			.filter(Boolean) as PickerOption[],
)
const filtered = computed(() => {
	const q = query.value.trim().toLowerCase()
	return q ? props.options.filter((o) => o.label.toLowerCase().includes(q)) : props.options
})

watch(open, async (isOpen) => {
	if (!isOpen) return
	query.value = ''
	active.value = Math.max(
		0,
		filtered.value.findIndex((o) => isSelected(o)),
	)
	await nextTick()
	searchEl.value?.focus()
})
watch(query, () => (active.value = 0))

function isSelected(opt: PickerOption) {
	return values.value.includes(opt.value)
}

function set(value: string | string[] | null) {
	model.value = value
	emit('change', value)
}

function pick(opt: PickerOption) {
	if (props.multiple) {
		const next = isSelected(opt)
			? values.value.filter((v) => v !== opt.value)
			: [...values.value, opt.value]
		set(next)
		return
	}
	set(opt.value)
	open.value = false
}

function pickActive() {
	const opt = filtered.value[active.value]
	if (opt) pick(opt)
}

function move(delta: number) {
	const n = filtered.value.length
	if (n) active.value = (active.value + delta + n) % n
}

function clear() {
	set(props.multiple ? [] : null)
	open.value = false
}
</script>
