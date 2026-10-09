<template>
	<StateIcon v-if="option.stateGroup" :group="option.stateGroup" :color="option.color" />
	<PriorityIcon v-else-if="option.priority" :priority="option.priority" small />
	<UserAvatar v-else-if="option.user" :user="option.user" size="xs" :tooltip="false" />
	<span v-else-if="option.emoji" class="text-sm leading-none">{{ option.emoji }}</span>
	<span v-else-if="option.icon" :class="option.icon" class="size-3.5 shrink-0 text-ink-gray-5" />
	<span
		v-else-if="option.color"
		class="size-2.5 shrink-0 rounded-full"
		:style="{ background: option.color }"
	/>
</template>

<script setup lang="ts">
import PriorityIcon from '@/components/common/PriorityIcon.vue'
import StateIcon from '@/components/common/StateIcon.vue'
import UserAvatar from '@/components/common/UserAvatar.vue'
import type { PickerOption } from './types'

defineProps<{ option: PickerOption }>()
</script>
