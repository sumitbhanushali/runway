export type StateGroup = 'Backlog' | 'Unstarted' | 'Started' | 'Completed' | 'Cancelled' | 'Triage'
export type Priority = 'Urgent' | 'High' | 'Medium' | 'Low' | 'None'
export type Role = 'Admin' | 'Member' | 'Guest'
export type Layout = 'list' | 'kanban' | 'spreadsheet'
export type GroupBy =
	| 'state'
	| 'state_group'
	| 'priority'
	| 'assignees'
	| 'labels'
	| 'cycle'
	| 'modules'
	| 'none'

export interface State {
	name: string
	title: string
	state_group: StateGroup
	color: string
	sequence: number
	is_default: 0 | 1
	description?: string
}

export interface Label {
	name: string
	title: string
	color: string
	parent_label?: string | null
}

export interface Member {
	user: string
	role: Role
	full_name: string
	user_image?: string | null
	email?: string
	name?: string
}

export interface CycleRef {
	name: string
	title: string
	status: 'Draft' | 'Upcoming' | 'Current' | 'Completed'
	start_date: string | null
	end_date: string | null
	completed_at: string | null
}

export interface ModuleRef {
	name: string
	title: string
	status: string
}

export interface Project {
	name: string
	workspace: string
	title: string
	identifier: string
	description?: string
	emoji?: string | null
	color?: string | null
	lead?: string | null
	default_assignee?: string | null
	network: 'Public' | 'Secret'
	estimate?: string | null
	archived: 0 | 1
	cycles_enabled: 0 | 1
	modules_enabled: 0 | 1
	views_enabled: 0 | 1
	intake_enabled: 0 | 1
	role: Role
	states: State[]
	labels: Label[]
	members: Member[]
	estimate_type: 'Categories' | 'Points' | null
	estimate_points: string[]
	cycles: CycleRef[]
	modules: ModuleRef[]
}

export interface Workspace {
	name: string
	title: string
	slug: string
	logo?: string | null
	role: Role
}

export interface Boot {
	user: { name: string; full_name: string; user_image?: string | null; email: string }
	is_admin: boolean
	workspaces: Workspace[]
	workspace: string | null
	projects: Project[]
	joinable_projects: Pick<Project, 'name' | 'title' | 'identifier' | 'emoji' | 'color'>[]
	members: Member[]
	favorites: { name: string; reference_doctype: string; reference_name: string }[]
	unread_count: number
}

export interface WorkItem {
	name: string
	project: string
	sequence_id: number
	title: string
	state: string
	state_group: StateGroup
	priority: Priority
	start_date: string | null
	due_date: string | null
	estimate_point: string | null
	cycle: string | null
	parent_item: string | null
	sort_order: number
	is_draft: 0 | 1
	archived_at: string | null
	completed_at: string | null
	owner: string
	creation: string
	modified: string
	assignees: string[]
	labels: string[]
	modules: string[]
	sub_items_count: number
	sub_items_done: number
	link_count: number
	attachment_count: number
}

export interface TimelineEntry {
	kind: 'activity' | 'comment'
	name: string
	creation: string
	actor?: string
	owner?: string
	verb?: string
	field?: string
	old_value?: string | null
	new_value?: string | null
	content?: string
	access?: 'Internal' | 'External'
	edited_at?: string | null
	reactions?: { emoji: string; user: string }[]
}

export interface Relation {
	name: string
	relation_type: string
	item: string
	detail: Pick<WorkItem, 'name' | 'title' | 'state' | 'state_group' | 'project' | 'priority'>
}

export interface WorkItemDetail extends WorkItem {
	description: string | null
	parent: WorkItem | null
	sub_items: WorkItem[]
	relations: Relation[]
	links: { name: string; title: string; url: string; owner: string; creation: string }[]
	attachments: {
		name: string
		file_name: string
		file_url: string
		file_size: number
		owner: string
		creation: string
	}[]
	is_subscribed: boolean
	intake: { name: string; status: string } | null
	timeline: TimelineEntry[]
	can_edit: boolean
}

export interface Filters {
	state?: string[]
	state_group?: StateGroup[]
	priority?: Priority[]
	assignees?: string[]
	labels?: string[]
	modules?: string[]
	cycle?: (string | null)[]
	owner?: string[]
	search?: string
	due?: 'overdue'
}

export interface DisplayFilters {
	layout: Layout
	group_by: GroupBy
	order_by: string
	show_sub_items: boolean
	show_empty_groups: boolean
}

export type DisplayProperty =
	| 'id'
	| 'state'
	| 'priority'
	| 'assignees'
	| 'labels'
	| 'start_date'
	| 'due_date'
	| 'estimate'
	| 'cycle'
	| 'modules'
	| 'sub_items'
	| 'links'
	| 'attachments'

export interface Progress {
	total: number
	completed: number
	percent: number
	by_group: Record<StateGroup, number>
	points_total: number
	points_completed: number
}

export interface Cycle extends CycleRef {
	project: string
	description?: string
	owner_user?: string | null
	progress: Progress
}

export interface Module {
	name: string
	project: string
	title: string
	description?: string | null
	status: string
	lead?: string | null
	members: string[]
	start_date?: string | null
	target_date?: string | null
	progress: Progress
}

export interface SavedView {
	name: string
	workspace: string
	project?: string | null
	title: string
	description?: string | null
	access: 'Private' | 'Public'
	filters?: string | null
	display_filters?: string | null
	display_properties?: string | null
	owner: string
}

export interface Notification {
	name: string
	work_item: string | null
	actor: string | null
	notification_type: string
	message: string
	read_at: string | null
	snoozed_until: string | null
	archived_at: string | null
	creation: string
	item?: { name: string; title: string; project: string; state_group: StateGroup } | null
}
