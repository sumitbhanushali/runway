import { computed, type Ref } from 'vue'
import { useWorkspace } from '@/stores/workspace'
import type { PickerOption } from '@/components/pickers/types'
import { PRIORITIES } from '@/utils/constants'

/** Picker options for one project's states, labels, members, cycles, modules and estimates. */
export function useProjectOptions(projectName: Ref<string | null | undefined>) {
	const ws = useWorkspace()
	const project = computed(() => ws.project(projectName.value))

	const states = computed<PickerOption[]>(() =>
		(project.value?.states ?? [])
			.filter((s) => s.state_group !== 'Triage')
			.map((s) => ({ value: s.name, label: s.title, stateGroup: s.state_group, color: s.color })),
	)
	const priorities = computed<PickerOption[]>(() =>
		PRIORITIES.map((p) => ({ value: p, label: p, priority: p })),
	)
	const members = computed<PickerOption[]>(() =>
		(project.value?.members ?? ws.members.value).map((m) => ({
			value: m.user,
			label: m.full_name || m.user,
			user: m.user,
		})),
	)
	const labels = computed<PickerOption[]>(() =>
		(project.value?.labels ?? []).map((l) => ({ value: l.name, label: l.title, color: l.color })),
	)
	const cycles = computed<PickerOption[]>(() =>
		(project.value?.cycles ?? [])
			.filter((c) => !c.completed_at)
			.map((c) => ({ value: c.name, label: c.title, icon: 'lucide-refresh-ccw' })),
	)
	const modules = computed<PickerOption[]>(() =>
		(project.value?.modules ?? []).map((m) => ({
			value: m.name,
			label: m.title,
			icon: 'lucide-boxes',
		})),
	)
	const estimates = computed<PickerOption[]>(() =>
		(project.value?.estimate_points ?? []).map((p) => ({
			value: p,
			label: p,
			icon: 'lucide-triangle',
		})),
	)

	function stateOf(name?: string | null) {
		return project.value?.states.find((s) => s.name === name)
	}
	function labelOf(name: string) {
		return project.value?.labels.find((l) => l.name === name)
	}
	function cycleOf(name?: string | null) {
		return project.value?.cycles.find((c) => c.name === name)
	}
	function moduleOf(name: string) {
		return project.value?.modules.find((m) => m.name === name)
	}

	return {
		project,
		states,
		priorities,
		members,
		labels,
		cycles,
		modules,
		estimates,
		stateOf,
		labelOf,
		cycleOf,
		moduleOf,
	}
}
