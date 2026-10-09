import type { WorkItem } from '@/types'

type Events = {
	'item-updated': WorkItem
	'item-created': WorkItem
	'item-deleted': string
	'create-item': { project?: string; defaults?: Partial<WorkItem> }
}
type Handler<T> = (payload: T) => void

const handlers: { [K in keyof Events]?: Set<Handler<Events[K]>> } = {}

/** App-wide events between the peek, dialogs and whichever boards are mounted. */
export const bus = {
	on<K extends keyof Events>(event: K, fn: Handler<Events[K]>) {
		;(handlers[event] ??= new Set() as never).add(fn as never)
		return () => handlers[event]?.delete(fn as never)
	},
	emit<K extends keyof Events>(event: K, payload: Events[K]) {
		handlers[event]?.forEach((fn) => (fn as Handler<Events[K]>)(payload))
	},
}
