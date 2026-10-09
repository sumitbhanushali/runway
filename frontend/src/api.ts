import { call } from 'frappe-ui'
import type {
	Boot,
	Cycle,
	Filters,
	Member,
	Module,
	Notification,
	Project,
	WorkItem,
	WorkItemDetail,
} from '@/types'

const m = (path: string) => `runway.api.${path}`

export const api = {
	boot: (workspace?: string | null) => call<Boot>(m('boot.get_boot'), { workspace }),
	getProject: (project: string) => call<Project>(m('boot.get_project'), { project }),
	createWorkspace: (title: string, slug: string) =>
		call<string>(m('boot.create_workspace'), { title, slug }),
	createProject: (args: {
		workspace: string
		title: string
		identifier: string
		description?: string
		network?: string
		emoji?: string
	}) => call<Project>(m('boot.create_project'), args),
	updateProject: (project: string, values: Record<string, unknown>) =>
		call<Project>(m('boot.update_project'), { project, values }),
	joinProject: (project: string) => call<Project>(m('boot.join_project'), { project }),
	projectMembers: (project: string) => call<Member[]>(m('boot.get_project_members'), { project }),
	addProjectMember: (project: string, user: string, role: string) =>
		call(m('boot.add_project_member'), { project, user, role }),
	removeProjectMember: (project: string, user: string) =>
		call(m('boot.remove_project_member'), { project, user }),
	inviteMember: (workspace: string, email: string, role: string) =>
		call<Member[]>(m('boot.invite_member'), { workspace, email, role }),
	updateWorkspaceMember: (workspace: string, user: string, role?: string, remove = false) =>
		call<Member[]>(m('boot.update_workspace_member'), { workspace, user, role, remove }),
	setEstimate: (project: string, estimate_type: string, points: string[]) =>
		call<Project>(m('boot.set_estimate'), { project, estimate_type, points }),
	toggleFavorite: (reference_doctype: string, reference_name: string) =>
		call<boolean>(m('boot.toggle_favorite'), { reference_doctype, reference_name }),
	recordVisit: (reference_doctype: string, reference_name: string) =>
		call(m('boot.record_visit'), { reference_doctype, reference_name }),

	items: (args: {
		project?: string
		workspace?: string
		filters?: Filters
		order_by?: string
		show_sub_items?: number
		show_archived?: number
		cycle?: string
		module?: string
		view?: string
	}) => call<WorkItem[]>(m('work_items.get_items'), args),
	createItem: (project: string, values: Record<string, unknown>) =>
		call<WorkItem>(m('work_items.create_item'), { project, values }),
	updateItem: (name: string, values: Record<string, unknown>) =>
		call<WorkItem>(m('work_items.update_item'), { name, values }),
	archiveItem: (name: string, restore = 0) =>
		call<WorkItem>(m('work_items.archive'), { name, restore }),
	deleteItem: (name: string) => call(m('work_items.delete_item'), { name }),
	detail: (name: string) => call<WorkItemDetail>(m('work_items.get_detail'), { name }),
	searchItems: (query: string, workspace?: string | null, project?: string) =>
		call<WorkItem[]>(m('work_items.search_items'), { query, workspace, project }),
	addRelation: (work_item: string, related_item: string, relation_type: string) =>
		call(m('work_items.add_relation'), { work_item, related_item, relation_type }),
	removeRelation: (name: string) => call(m('work_items.remove_relation'), { name }),
	addLink: (work_item: string, url: string, title?: string) =>
		call(m('work_items.add_link'), { work_item, url, title }),
	removeLink: (name: string) => call(m('work_items.remove_link'), { name }),
	removeAttachment: (file_name: string) => call(m('work_items.remove_attachment'), { file_name }),
	toggleSubscription: (work_item: string) =>
		call<boolean>(m('work_items.toggle_subscription'), { work_item }),
	addComment: (work_item: string, content: string, access = 'Internal') =>
		call<string>(m('work_items.add_comment'), { work_item, content, access }),
	updateComment: (name: string, content: string) =>
		call(m('work_items.update_comment'), { name, content }),
	deleteComment: (name: string) => call(m('work_items.delete_comment'), { name }),
	toggleReaction: (reference_name: string, emoji: string) =>
		call<boolean>(m('work_items.toggle_reaction'), {
			reference_doctype: 'Runway Comment',
			reference_name,
			emoji,
		}),

	cycles: (project: string) => call<Cycle[]>(m('cycles.get_cycles'), { project }),
	burndown: (cycle: string, by: 'count' | 'points') =>
		call<{ days: string[]; ideal: number[]; actual: (number | null)[]; total: number }>(
			m('cycles.get_burndown'),
			{ cycle, by },
		),
	completeCycle: (cycle: string, transfer_to?: string | null) =>
		call<{ transferred: number; pending: number }>(m('cycles.complete_cycle'), {
			cycle,
			transfer_to,
		}),

	modules: (project: string) => call<Module[]>(m('modules.get_modules'), { project }),
	module: (name: string) => call<Module>(m('modules.get_module'), { name }),

	intake: (project: string, status: string) =>
		call<
			{
				name: string
				work_item: string
				status: string
				snoozed: boolean
				snoozed_till: string | null
				source: string
				submitted_by: string
				creation: string
				item: { name: string; title: string; priority: string } | null
			}[]
		>(m('intake.get_intake'), { project, status }),
	submitIntake: (project: string, title: string, description?: string, priority?: string) =>
		call<string>(m('intake.submit'), { project, title, description, priority }),
	acceptIntake: (intake: string) => call(m('intake.accept'), { intake }),
	declineIntake: (intake: string) => call(m('intake.decline'), { intake }),
	snoozeIntake: (intake: string, until: string | null) =>
		call(m('intake.snooze'), { intake, until }),
	duplicateIntake: (intake: string, duplicate_of: string) =>
		call(m('intake.mark_duplicate'), { intake, duplicate_of }),

	analytics: (args: {
		workspace?: string | null
		project?: string | null
		x_axis: string
		y_axis: string
		segment?: string | null
	}) =>
		call<{
			rows: { key: string | null; label: string; value: number; segments: Record<string, number> }[]
			segments: { key: string; label: string }[]
			total_items: number
			summary: Record<string, number>
		}>(m('analytics.get_analytics'), args),
	exportCsv: (args: { workspace?: string | null; project?: string | null; filters?: Filters }) =>
		call<string>(m('analytics.export_csv'), args),

	inbox: (tab: string) => call<Notification[]>(m('notifications.get_inbox'), { tab }),
	markRead: (names: string[], unread = 0) => call(m('notifications.mark_read'), { names, unread }),
	markAllRead: () => call(m('notifications.mark_all_read')),
	archiveNotification: (names: string[], unarchive = 0) =>
		call(m('notifications.archive'), { names, unarchive }),
	snoozeNotification: (names: string[], until: string | null) =>
		call(m('notifications.snooze'), { names, until }),
	unreadCount: () => call<number>(m('notifications.unread_count')),

	myWork: (workspace: string, tab: string, filters?: Filters, order_by?: string) =>
		call<WorkItem[]>(m('my_work.get_my_work'), { workspace, tab, filters, order_by }),
	home: (workspace: string) =>
		call<{
			counts: { open: number; overdue: number; due_this_week: number; completed: number }
			upcoming: WorkItem[]
			recents: {
				reference_doctype: string
				reference_name: string
				title: string
				visited_at: string
			}[]
		}>(m('my_work.get_home'), { workspace }),

	// Generic document CRUD for simple doctypes (cycles, modules, views, states, labels).
	insert: <T = Record<string, unknown>>(doc: Record<string, unknown>) =>
		call<T>('frappe.client.insert', { doc }),
	setValue: <T = Record<string, unknown>>(
		doctype: string,
		name: string,
		fieldname: Record<string, unknown>,
	) => call<T>('frappe.client.set_value', { doctype, name, fieldname }),
	remove: (doctype: string, name: string) => call('frappe.client.delete', { doctype, name }),
	getList: <T = Record<string, unknown>>(
		doctype: string,
		args: { fields?: string[]; filters?: unknown; order_by?: string; limit_page_length?: number },
	) => call<T[]>('frappe.client.get_list', { doctype, ...args }),
	getDoc: <T = Record<string, unknown>>(doctype: string, name: string) =>
		call<T>('frappe.client.get', { doctype, name }),
}

export function errorMessage(e: unknown): string {
	const err = e as { messages?: string[]; message?: string; exc_type?: string }
	if (err?.messages?.length) return err.messages.join('\n').replace(/<[^>]+>/g, '')
	return err?.message || 'Something went wrong'
}
