import type { Priority, StateGroup } from '@/types'

export interface PickerOption {
	value: string
	label: string
	/** A lucide-* class. */
	icon?: string
	/** Dot / swatch color. */
	color?: string | null
	/** Renders a user avatar. */
	user?: string
	stateGroup?: StateGroup
	priority?: Priority
	emoji?: string | null
}
