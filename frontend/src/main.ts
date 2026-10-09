import { createApp } from 'vue'
import { FrappeUI, call, setConfig } from 'frappe-ui'
import App from './App.vue'
import router from './router'
import './style.css'

/**
 * In production `frappe-ui/vite`'s jinjaBootData plugin writes every key of
 * `runway/www/runway.py`'s boot dict onto `window`. The dev server serves
 * `index.html` verbatim, so fetch the same dict over the API instead.
 */
async function loadDevBootData() {
	if (!import.meta.env.DEV) return
	try {
		const boot = await call<Record<string, unknown>>('runway.www.runway.get_context_for_dev')
		Object.assign(window, boot)
	} catch {
		// Only available while `developer_mode` is on; the app runs fine without it.
	}
}

async function start() {
	await loadDevBootData()
	setConfig('systemTimezone', window.system_timezone ?? null)

	const app = createApp(App)
	app.use(router)
	app.use(FrappeUI)
	app.mount('#app')
}

start()
