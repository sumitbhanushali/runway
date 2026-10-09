import { reactive, watch } from 'vue'
import type { DisplayFilters, DisplayProperty, Filters } from '@/types'

export interface DisplayState {
	filters: Filters
	display: DisplayFilters
	properties: DisplayProperty[]
}

export const DEFAULT_PROPERTIES: DisplayProperty[] = [
	'id',
	'state',
	'priority',
	'assignees',
	'labels',
	'due_date',
	'estimate',
	'sub_items',
]

export function defaultDisplay(): DisplayState {
	return {
		filters: {},
		display: {
			layout: 'list',
			group_by: 'state',
			order_by: 'sort_order',
			show_sub_items: true,
			show_empty_groups: true,
		},
		properties: [...DEFAULT_PROPERTIES],
	}
}

function read(key: string): DisplayState | null {
	try {
		const raw = localStorage.getItem(`runway:display:${key}`)
		return raw ? (JSON.parse(raw) as DisplayState) : null
	} catch {
		return null
	}
}

/** Filters, layout and visible properties for one scope, remembered per browser. */
export function useDisplay(key: string, initial?: Partial<DisplayState>) {
	const base = defaultDisplay()
	const saved = read(key)
	const state = reactive<DisplayState>({
		filters: { ...base.filters, ...(initial?.filters ?? {}), ...(saved?.filters ?? {}) },
		display: { ...base.display, ...(initial?.display ?? {}), ...(saved?.display ?? {}) },
		properties: saved?.properties ?? initial?.properties ?? base.properties,
	})
	watch(
		state,
		() => {
			try {
				localStorage.setItem(`runway:display:${key}`, JSON.stringify(state))
			} catch {
				/* storage can be unavailable; the view still works */
			}
		},
		{ deep: true },
	)
	return state
}

export function activeFilterCount(filters: Filters) {
	return Object.entries(filters).filter(
		([k, v]) => k !== 'search' && (Array.isArray(v) ? v.length : !!v),
	).length
}
