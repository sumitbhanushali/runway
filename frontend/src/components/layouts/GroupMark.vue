<template>
	<StateIcon v-if="group.stateGroup" :group="group.stateGroup" :color="group.color" />
	<PriorityIcon v-else-if="group.priority" :priority="group.priority" small />
	<UserAvatar v-else-if="group.user" :user="group.user" size="xs" :tooltip="false" />
	<span v-else-if="group.icon" :class="group.icon" class="size-3.5 text-ink-gray-5" />
	<span
		v-else-if="group.color"
		class="size-2.5 rounded-full"
		:style="{ background: group.color }"
	/>
</template>

<script setup lang="ts">
import PriorityIcon from '@/components/common/PriorityIcon.vue'
import StateIcon from '@/components/common/StateIcon.vue'
import UserAvatar from '@/components/common/UserAvatar.vue'
import type { ItemGroup } from '@/utils/grouping'

defineProps<{ group: ItemGroup }>()
</script>
