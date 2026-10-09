<template>
	<span :class="[meta.icon, meta.color, sizeClass]" class="shrink-0" aria-hidden="true" />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Priority } from '@/types'
import { PRIORITY_META } from '@/utils/constants'

const props = withDefaults(defineProps<{ priority: Priority; small?: boolean }>(), { small: false })
const meta = computed(() => PRIORITY_META[props.priority] ?? PRIORITY_META.None)
const sizeClass = computed(() => (props.small ? 'size-3.5' : 'size-4'))
</script>
