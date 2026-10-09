<template>
	<router-link v-slot="{ href, navigate, isActive, isExactActive }" :to="to" custom>
		<a
			:href="href"
			class="flex items-center gap-2 rounded-4 px-2 text-sm"
			:class="[
				small ? 'py-1' : 'py-1.5',
				(exact ? isExactActive : isActive)
					? 'bg-surface-base font-medium text-ink-gray-9 shadow-sm'
					: 'text-ink-gray-7 hover:bg-surface-gray-3',
			]"
			@click="navigate"
		>
			<span v-if="emoji" class="w-4 text-center text-sm leading-none">{{ emoji }}</span>
			<span v-else :class="icon" class="size-4 shrink-0 text-ink-gray-6" />
			<span class="flex-1 truncate">{{ label }}</span>
			<span
				v-if="badge"
				class="rounded-full bg-surface-gray-7 px-1.5 text-xs font-medium text-ink-base"
				>{{ badge }}</span
			>
		</a>
	</router-link>
</template>

<script setup lang="ts">
import type { RouteLocationRaw } from 'vue-router'

defineProps<{
	to: RouteLocationRaw
	icon: string
	label: string
	emoji?: string
	badge?: number
	small?: boolean
	exact?: boolean
}>()
</script>
