import { onScopeDispose, ref, shallowRef, watch, type Ref } from 'vue'
import { toast } from 'frappe-ui'
import { api, errorMessage } from '@/api'
import type { Filters, WorkItem } from '@/types'
import { onRealtime, subscribeDoc } from '@/utils/socket'

export interface ItemsQuery {
	project?: string
	workspace?: string
	cycle?: string
	module?: string
	view?: string
	myWork?: string
	filters: Filters
	order_by: string
	show_sub_items: boolean
}

/**
 * A live list of work items for any scope (project, cycle, module, view, my work).
 * Updates are applied optimistically and rolled back if the server refuses them.
 */
export function useWorkItems(query: Ref<ItemsQuery | null>) {
	const items = ref<WorkItem[]>([])
	const loading = ref(false)
	const loaded = shallowRef(false)
	let seq = 0

	async function reload() {
		const q = query.value
		if (!q) return
		const mine = ++seq
		loading.value = true
		try {
			const rows = q.myWork
				? await api.myWork(q.workspace!, q.myWork, q.filters, q.order_by)
				: await api.items({
						project: q.project,
						workspace: q.workspace,
						cycle: q.cycle,
						module: q.module,
						view: q.view,
						filters: q.filters,
						order_by: q.order_by,
						show_sub_items: q.show_sub_items ? 1 : 0,
					})
			if (mine === seq) {
				items.value = rows
				loaded.value = true
			}
		} catch (e) {
			toast.error(errorMessage(e))
		} finally {
			if (mine === seq) loading.value = false
		}
	}

	watch(query, reload, { deep: true, immediate: true })

	function replace(row: WorkItem) {
		const idx = items.value.findIndex((i) => i.name === row.name)
		if (idx >= 0) items.value.splice(idx, 1, row)
	}

	async function update(name: string, values: Partial<WorkItem>) {
		const idx = items.value.findIndex((i) => i.name === name)
		const before = idx >= 0 ? { ...items.value[idx] } : null
		if (idx >= 0) items.value.splice(idx, 1, { ...items.value[idx], ...values })
		try {
			const row = await api.updateItem(name, values as Record<string, unknown>)
			replace(row)
			return row
		} catch (e) {
			if (before) replace(before)
			toast.error(errorMessage(e))
			throw e
		}
	}

	async function create(project: string, values: Partial<WorkItem>) {
		try {
			const row = await api.createItem(project, values as Record<string, unknown>)
			items.value.push(row)
			return row
		} catch (e) {
			toast.error(errorMessage(e))
			throw e
		}
	}

	function remove(name: string) {
		items.value = items.value.filter((i) => i.name !== name)
	}

	// Someone else changed an item in a project we are showing: refetch quietly.
	let timer: ReturnType<typeof setTimeout> | undefined
	const off = onRealtime('runway_item_updated', (data: { name: string; project: string }) => {
		const q = query.value
		if (!q) return
		if (q.project && q.project !== data.project) return
		clearTimeout(timer)
		timer = setTimeout(reload, 400)
	})
	// Project-scoped broadcasts go to the project's document room.
	let unsubscribe: (() => void) | undefined
	watch(
		() => query.value?.project,
		(project) => {
			unsubscribe?.()
			unsubscribe = project ? subscribeDoc('Runway Project', project) : undefined
		},
		{ immediate: true },
	)
	onScopeDispose(() => {
		off()
		unsubscribe?.()
		clearTimeout(timer)
	})

	return { items, loading, loaded, reload, update, create, remove, replace }
}

export type WorkItemsStore = ReturnType<typeof useWorkItems>
