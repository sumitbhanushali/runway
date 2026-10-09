<template>
	<span
		class="inline-flex shrink-0 items-center justify-center rounded-2 text-xs font-semibold"
		:class="project?.emoji ? '' : 'bg-surface-gray-3 text-ink-gray-7'"
		:style="{
			width: `${size}px`,
			height: `${size}px`,
			fontSize: project?.emoji ? `${size - 4}px` : undefined,
		}"
	>
		{{ project?.emoji || (project?.identifier || '?').slice(0, 2) }}
	</span>
</template>

<script setup lang="ts">
withDefaults(
	defineProps<{
		project?: { emoji?: string | null; identifier?: string } | null
		size?: number
	}>(),
	{ size: 20 },
)
</script>
