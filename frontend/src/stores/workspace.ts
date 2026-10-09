import { computed, reactive } from 'vue'
import { api } from '@/api'
import type { Boot, Member, Project } from '@/types'

interface WorkspaceState {
	boot: Boot | null
	loading: boolean
	error: string | null
}

const state = reactive<WorkspaceState>({ boot: null, loading: false, error: null })

let inflight: Promise<Boot> | null = null

/** Loads (or reloads) the shell data for a workspace. */
export async function loadBoot(workspace?: string | null, force = false): Promise<Boot> {
	if (!force && state.boot && (!workspace || state.boot.workspace === workspace)) return state.boot
	if (inflight) return inflight
	state.loading = true
	inflight = api.boot(workspace)
	try {
		const boot = await inflight
		state.boot = boot
		state.error = null
		return boot
	} catch (e) {
		state.error = (e as Error).message
		throw e
	} finally {
		state.loading = false
		inflight = null
	}
}

/** Re-fetches a single project (states, labels, members, cycles...) after an edit. */
export async function refreshProject(name: string): Promise<Project | null> {
	if (!state.boot) return null
	const project = await api.getProject(name)
	upsertProject(project)
	return project
}

export function upsertProject(project: Project) {
	if (!state.boot) return
	const idx = state.boot.projects.findIndex((p) => p.name === project.name)
	if (idx >= 0) state.boot.projects.splice(idx, 1, project)
	else state.boot.projects.push(project)
	state.boot.joinable_projects = state.boot.joinable_projects.filter((p) => p.name !== project.name)
}

const projectsByName = computed(() => {
	const map: Record<string, Project> = {}
	for (const p of state.boot?.projects ?? []) map[p.name] = p
	return map
})

const membersByUser = computed(() => {
	const map: Record<string, Member> = {}
	for (const m of state.boot?.members ?? []) map[m.user] = m
	for (const p of state.boot?.projects ?? []) for (const m of p.members) map[m.user] ??= m
	return map
})

export function useWorkspace() {
	return {
		state,
		boot: computed(() => state.boot),
		workspace: computed(() => state.boot?.workspace ?? null),
		workspaceDoc: computed(() =>
			state.boot?.workspaces.find((w) => w.name === state.boot?.workspace),
		),
		user: computed(() => state.boot?.user),
		projects: computed(() => (state.boot?.projects ?? []).filter((p) => !p.archived)),
		allProjects: computed(() => state.boot?.projects ?? []),
		members: computed(() => state.boot?.members ?? []),
		project: (name?: string | null) => (name ? projectsByName.value[name] : undefined),
		member: (user?: string | null) => (user ? membersByUser.value[user] : undefined),
		userName: (user?: string | null) =>
			(user && membersByUser.value[user]?.full_name) || user || '',
		isFavorite: (doctype: string, name: string) =>
			(state.boot?.favorites ?? []).some(
				(f) => f.reference_doctype === doctype && f.reference_name === name,
			),
		async toggleFavorite(doctype: string, name: string) {
			const on = await api.toggleFavorite(doctype, name)
			if (!state.boot) return
			if (on) state.boot.favorites.push({ name, reference_doctype: doctype, reference_name: name })
			else
				state.boot.favorites = state.boot.favorites.filter(
					(f) => !(f.reference_doctype === doctype && f.reference_name === name),
				)
		},
		setUnread(n: number) {
			if (state.boot) state.boot.unread_count = n
		},
	}
}
