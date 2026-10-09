<template>
	<div class="flex items-center">
		<div
			v-for="(u, i) in shown"
			:key="u"
			:class="i ? '-ml-1.5' : ''"
			class="rounded-full ring-2 ring-surface-base"
		>
			<UserAvatar :user="u" size="xs" />
		</div>
		<span v-if="users.length > max" class="ml-1 text-xs text-ink-gray-5"
			>+{{ users.length - max }}</span
		>
	</div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import UserAvatar from './UserAvatar.vue'

const props = withDefaults(defineProps<{ users: string[]; max?: number }>(), { max: 3 })
const shown = computed(() => props.users.slice(0, props.max))
</script>
