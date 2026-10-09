<template>
	<header
		class="flex h-12 shrink-0 items-center justify-between gap-3 border-b border-outline-gray-1 bg-surface-base px-4"
	>
		<div class="flex min-w-0 items-center gap-1.5 text-base">
			<template v-for="(crumb, i) in crumbs" :key="i">
				<span v-if="i" class="text-ink-gray-4">/</span>
				<router-link
					v-if="crumb.route && i < crumbs.length - 1"
					:to="crumb.route"
					class="flex min-w-0 items-center gap-1.5 truncate text-ink-gray-5 hover:text-ink-gray-8"
				>
					<span v-if="crumb.icon" :class="crumb.icon" class="size-4" />
					{{ crumb.label }}
				</router-link>
				<span
					v-else
					class="flex min-w-0 items-center gap-1.5 truncate font-medium text-ink-gray-9"
				>
					<span v-if="crumb.icon" :class="crumb.icon" class="size-4" />
					{{ crumb.label }}
				</span>
			</template>
			<slot name="after-title" />
		</div>
		<div class="flex shrink-0 items-center gap-2">
			<slot name="actions" />
		</div>
	</header>
</template>

<script setup lang="ts">
import type { RouteLocationRaw } from 'vue-router'

defineProps<{ crumbs: { label: string; route?: RouteLocationRaw; icon?: string }[] }>()
</script>
