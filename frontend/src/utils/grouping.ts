import type { GroupBy, Priority, Project, StateGroup, WorkItem } from '@/types'
import { PRIORITIES, STATE_GROUPS, STATE_GROUP_COLORS } from './constants'

export interface ItemGroup {
	key: string
	label: string
	stateGroup?: StateGroup
	color?: string | null
	priority?: Priority
	user?: string
	icon?: string
	items: WorkItem[]
	/** Field values a new item created in this group should start with. */
	defaults: Partial<WorkItem>
}

const NONE = '__none__'

export function groupItems(
	items: WorkItem[],
	groupBy: GroupBy,
	opts: { project?: Project; userName: (u: string) => string; showEmpty?: boolean },
): ItemGroup[] {
	const { project } = opts
	if (groupBy === 'state' && !project) groupBy = 'state_group'

	if (groupBy === 'none') {
		return [{ key: 'all', label: 'All work items', items, defaults: {} }]
	}

	const groups = new Map<string, ItemGroup>()
	const add = (g: Omit<ItemGroup, 'items'>) => {
		if (!groups.has(g.key)) groups.set(g.key, { ...g, items: [] })
		return groups.get(g.key)!
	}

	// Seed groups in their natural order so empty ones still show up (Kanban columns).
	if (groupBy === 'state' && project) {
		for (const s of project.states.filter((s) => s.state_group !== 'Triage'))
			add({
				key: s.name,
				label: s.title,
				stateGroup: s.state_group,
				color: s.color,
				defaults: { state: s.name },
			})
	} else if (groupBy === 'state_group') {
		for (const g of STATE_GROUPS)
			add({ key: g, label: g, stateGroup: g, color: STATE_GROUP_COLORS[g], defaults: {} })
	} else if (groupBy === 'priority') {
		for (const p of PRIORITIES) add({ key: p, label: p, priority: p, defaults: { priority: p } })
	} else if (groupBy === 'assignees' && project) {
		for (const m of project.members)
			add({
				key: m.user,
				label: m.full_name || m.user,
				user: m.user,
				defaults: { assignees: [m.user] },
			})
	} else if (groupBy === 'labels' && project) {
		for (const l of project.labels)
			add({ key: l.name, label: l.title, color: l.color, defaults: { labels: [l.name] } })
	} else if (groupBy === 'cycle' && project) {
		for (const c of project.cycles.filter((c) => !c.completed_at))
			add({ key: c.name, label: c.title, icon: 'lucide-refresh-ccw', defaults: { cycle: c.name } })
	} else if (groupBy === 'modules' && project) {
		for (const m of project.modules)
			add({ key: m.name, label: m.title, icon: 'lucide-boxes', defaults: { modules: [m.name] } })
	}

	const noneGroup = () =>
		add({
			key: NONE,
			label: `No ${groupBy === 'assignees' ? 'assignee' : groupBy === 'modules' ? 'module' : groupBy === 'labels' ? 'label' : groupBy}`,
			icon: 'lucide-circle-dashed',
			defaults: {},
		})

	for (const item of items) {
		let keys: (string | null)[]
		switch (groupBy) {
			case 'assignees':
			case 'labels':
			case 'modules':
				keys = item[groupBy].length ? item[groupBy] : [null]
				break
			case 'state':
				keys = [item.state]
				break
			case 'state_group':
				keys = [item.state_group]
				break
			case 'priority':
				keys = [item.priority]
				break
			case 'cycle':
				keys = [item.cycle]
				break
			default:
				keys = [null]
		}
		for (const key of keys) {
			if (key === null) {
				noneGroup().items.push(item)
				continue
			}
			let g = groups.get(key)
			if (!g) {
				// A value we did not seed (other project, completed cycle, ex-member...).
				g = add({
					key,
					label: groupBy === 'assignees' ? opts.userName(key) : key,
					user: groupBy === 'assignees' ? key : undefined,
					defaults: {},
				})
			}
			g.items.push(item)
		}
	}

	if (
		groupBy === 'assignees' ||
		groupBy === 'labels' ||
		groupBy === 'modules' ||
		groupBy === 'cycle'
	)
		noneGroup()
	const list = [...groups.values()]
	return opts.showEmpty === false ? list.filter((g) => g.items.length) : list
}
