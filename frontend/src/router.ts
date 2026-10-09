import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { loadBoot } from '@/stores/workspace'

const page = (name: string, path: string, component: () => Promise<unknown>): RouteRecordRaw =>
	({ name, path, component, props: true }) as RouteRecordRaw

const routes: RouteRecordRaw[] = [
	{
		path: '/',
		name: 'Root',
		component: () => import('@/pages/RootRedirect.vue'),
	},
	{
		path: '/onboarding',
		name: 'Onboarding',
		component: () => import('@/pages/OnboardingPage.vue'),
	},
	{
		path: '/:workspace',
		component: () => import('@/pages/AppLayout.vue'),
		props: true,
		children: [
			page('Home', '', () => import('@/pages/HomePage.vue')),
			page('Inbox', 'inbox', () => import('@/pages/InboxPage.vue')),
			page('MyWork', 'my-work/:tab?', () => import('@/pages/MyWorkPage.vue')),
			page('Analytics', 'analytics', () => import('@/pages/AnalyticsPage.vue')),
			page('WorkspaceViews', 'views', () => import('@/pages/ViewsPage.vue')),
			page('WorkspaceView', 'views/:view', () => import('@/pages/ViewDetailPage.vue')),
			page('WorkspaceSettings', 'settings', () => import('@/pages/WorkspaceSettingsPage.vue')),
			page('Projects', 'projects', () => import('@/pages/ProjectsPage.vue')),
			page(
				'ProjectItems',
				'projects/:project/work-items',
				() => import('@/pages/ProjectItemsPage.vue'),
			),
			page('Cycles', 'projects/:project/cycles', () => import('@/pages/CyclesPage.vue')),
			page('Cycle', 'projects/:project/cycles/:cycle', () => import('@/pages/CycleDetailPage.vue')),
			page('Modules', 'projects/:project/modules', () => import('@/pages/ModulesPage.vue')),
			page(
				'Module',
				'projects/:project/modules/:module',
				() => import('@/pages/ModuleDetailPage.vue'),
			),
			page('ProjectViews', 'projects/:project/views', () => import('@/pages/ViewsPage.vue')),
			page(
				'ProjectView',
				'projects/:project/views/:view',
				() => import('@/pages/ViewDetailPage.vue'),
			),
			page('Intake', 'projects/:project/intake', () => import('@/pages/IntakePage.vue')),
			page(
				'ProjectSettings',
				'projects/:project/settings/:tab?',
				() => import('@/pages/ProjectSettingsPage.vue'),
			),
			page('WorkItem', 'browse/:item', () => import('@/pages/WorkItemPage.vue')),
		],
	},
]

const router = createRouter({
	history: createWebHistory('/runway'),
	routes,
})

router.beforeEach(async (to) => {
	if (to.name === 'Onboarding') return true
	const workspace = to.params.workspace as string | undefined
	try {
		const boot = await loadBoot(workspace)
		if (!boot.workspaces.length) return { name: 'Onboarding' }
		// An unknown or inaccessible slug falls back to the user's first workspace.
		if (to.name === 'Root' || (workspace && boot.workspace !== workspace)) {
			return { name: 'Home', params: { workspace: boot.workspace! } }
		}
	} catch {
		window.location.href = `/login?redirect-to=${encodeURIComponent(window.location.pathname)}`
		return false
	}
	return true
})

export default router
