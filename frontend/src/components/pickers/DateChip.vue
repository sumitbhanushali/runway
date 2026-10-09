<template>
	<DatePicker
		:model-value="modelValue || ''"
		:disabled="disabled"
		clearable
		@update:model-value="(v: string) => emit('update:modelValue', v || null)"
	>
		<template #trigger="{ toggle }">
			<button
				type="button"
				:disabled="disabled"
				class="flex h-6 items-center gap-1.5 rounded-3 px-1.5 text-sm transition-colors hover:bg-surface-gray-2 disabled:hover:bg-transparent"
				:class="[
					overdue ? 'text-ink-red-4' : modelValue ? 'text-ink-gray-7' : 'text-ink-gray-4',
					bordered ? 'border border-outline-gray-2' : '',
				]"
				@click.stop="toggle"
			>
				<span :class="icon" class="size-3.5" />
				<span>{{
					modelValue ? dayjs(modelValue).format('MMM D, YYYY') : placeholder
				}}</span>
			</button>
		</template>
	</DatePicker>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { DatePicker, dayjs } from 'frappe-ui'

const props = withDefaults(
	defineProps<{
		modelValue: string | null
		placeholder?: string
		icon?: string
		disabled?: boolean
		bordered?: boolean
		/** Highlight past dates (for due dates on open items). */
		warnPast?: boolean
	}>(),
	{
		placeholder: 'Set date',
		icon: 'lucide-calendar',
		disabled: false,
		bordered: false,
		warnPast: false,
	},
)
const emit = defineEmits<{ 'update:modelValue': [value: string | null] }>()

const overdue = computed(
	() => props.warnPast && !!props.modelValue && dayjs(props.modelValue).isBefore(dayjs(), 'day'),
)
</script>
