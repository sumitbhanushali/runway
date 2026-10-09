export const BUILT_IN = [
	{ name: 'all', title: 'All work items', icon: 'lucide-layers-2', myWork: undefined },
	{ name: 'assigned', title: 'Assigned to me', icon: 'lucide-user-check', myWork: 'assigned' },
	{ name: 'created', title: 'Created by me', icon: 'lucide-pencil-line', myWork: 'created' },
	{ name: 'subscribed', title: 'Subscribed', icon: 'lucide-bell', myWork: 'subscribed' },
] as const
