import type { DisplayProperty, GroupBy, Priority, StateGroup } from '@/types'

export const STATE_GROUPS: StateGroup[] = [
	'Backlog',
	'Unstarted',
	'Started',
	'Completed',
	'Cancelled',
]

export const STATE_GROUP_COLORS: Record<StateGroup, string> = {
	Backlog: '#a3a3a3',
	Unstarted: '#3a3a3a',
	Started: '#f59e0b',
	Completed: '#16a34a',
	Cancelled: '#9ca3af',
	Triage: '#4e5355',
}

export const PRIORITIES: Priority[] = ['Urgent', 'High', 'Medium', 'Low', 'None']

export const PRIORITY_META: Record<Priority, { icon: string; color: string }> = {
	Urgent: { icon: 'lucide-circle-alert', color: 'text-ink-red-4' },
	High: { icon: 'lucide-signal-high', color: 'text-ink-amber-3' },
	Medium: { icon: 'lucide-signal-medium', color: 'text-ink-amber-3' },
	Low: { icon: 'lucide-signal-low', color: 'text-ink-blue-3' },
	None: { icon: 'lucide-ban', color: 'text-ink-gray-4' },
}

export const GROUP_BY_OPTIONS: { label: string; value: GroupBy }[] = [
	{ label: 'States', value: 'state' },
	{ label: 'State groups', value: 'state_group' },
	{ label: 'Priority', value: 'priority' },
	{ label: 'Assignees', value: 'assignees' },
	{ label: 'Labels', value: 'labels' },
	{ label: 'Cycle', value: 'cycle' },
	{ label: 'Modules', value: 'modules' },
	{ label: 'None', value: 'none' },
]

export const ORDER_BY_OPTIONS = [
	{ label: 'Manual', value: 'sort_order' },
	{ label: 'Last created', value: '-creation' },
	{ label: 'Last updated', value: '-modified' },
	{ label: 'Start date', value: 'start_date' },
	{ label: 'Due date', value: 'due_date' },
	{ label: 'Priority', value: 'priority' },
]

export const DISPLAY_PROPERTIES: { label: string; value: DisplayProperty }[] = [
	{ label: 'ID', value: 'id' },
	{ label: 'State', value: 'state' },
	{ label: 'Priority', value: 'priority' },
	{ label: 'Assignees', value: 'assignees' },
	{ label: 'Labels', value: 'labels' },
	{ label: 'Start date', value: 'start_date' },
	{ label: 'Due date', value: 'due_date' },
	{ label: 'Estimate', value: 'estimate' },
	{ label: 'Cycle', value: 'cycle' },
	{ label: 'Modules', value: 'modules' },
	{ label: 'Sub-work items', value: 'sub_items' },
	{ label: 'Links', value: 'links' },
	{ label: 'Attachments', value: 'attachments' },
]

export const MODULE_STATUSES = [
	'Backlog',
	'Planned',
	'In Progress',
	'Paused',
	'Completed',
	'Cancelled',
]

export const RELATION_TYPES = [
	{ label: 'Blocked by', value: 'blocked_by' },
	{ label: 'Blocking', value: 'blocking' },
	{ label: 'Relates to', value: 'relates_to' },
	{ label: 'Duplicate of', value: 'duplicate' },
	{ label: 'Starts before', value: 'start_before' },
	{ label: 'Starts after', value: 'start_after' },
	{ label: 'Finishes before', value: 'finish_before' },
	{ label: 'Finishes after', value: 'finish_after' },
	{ label: 'Implemented by', value: 'implemented_by' },
	{ label: 'Implements', value: 'implements' },
]

export const REACTIONS = ['👍', '👎', '🎉', '❤️', '🚀', '👀']
