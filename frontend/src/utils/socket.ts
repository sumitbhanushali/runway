import { io, type Socket } from 'socket.io-client'

let socket: Socket | null = null

/** One socket.io connection to Frappe's realtime server, opened on first use. */
export function getSocket(): Socket | null {
	if (socket) return socket
	const site = window.site_name
	if (!site) return null
	const { protocol, hostname, port } = window.location
	// In development Frappe's socket server listens on its own port; behind a
	// proxy it shares the page's origin.
	const devPort = import.meta.env.DEV || port ? window.socketio_port : undefined
	const host = devPort
		? `${protocol}//${hostname}:${devPort}`
		: `${protocol}//${hostname}${port ? `:${port}` : ''}`
	socket = io(`${host}/${site}`, { withCredentials: true, reconnectionAttempts: 5 })
	return socket
}

export function onRealtime<T = unknown>(event: string, handler: (data: T) => void) {
	const s = getSocket()
	s?.on(event, handler)
	return () => s?.off(event, handler)
}

export function subscribeDoc(doctype: string, name: string) {
	getSocket()?.emit('doc_subscribe', doctype, name)
	return () => getSocket()?.emit('doc_unsubscribe', doctype, name)
}
