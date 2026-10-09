<template>
	<div class="flex flex-1 flex-col items-center justify-center gap-3 px-6 py-16 text-center">
		<span v-if="icon" :class="icon" class="size-10 text-ink-gray-4" />
		<div class="text-lg font-medium text-ink-gray-8">{{ title }}</div>
		<p v-if="description" class="max-w-md text-p-base text-ink-gray-5">{{ description }}</p>
		<slot />
	</div>
</template>

<script setup lang="ts">
defineProps<{ title: string; description?: string; icon?: string }>()
</script>
