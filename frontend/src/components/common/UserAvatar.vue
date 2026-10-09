<template>
	<Tooltip :text="tooltip ? name : undefined" :disabled="!tooltip">
		<Avatar
			:image="member?.user_image || undefined"
			:label="name"
			:size="size"
			shape="circle"
		/>
	</Tooltip>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Avatar, Tooltip } from 'frappe-ui'
import { useWorkspace } from '@/stores/workspace'

const props = withDefaults(
	defineProps<{ user: string; size?: 'xs' | 'sm' | 'md' | 'lg'; tooltip?: boolean }>(),
	{ size: 'sm', tooltip: true },
)

const ws = useWorkspace()
const member = computed(() => ws.member(props.user))
const name = computed(() => ws.userName(props.user))
</script>
