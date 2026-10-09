## Runway

Plane-style project management for Frappe: workspaces, projects, work items (sub-items, relations,
comments, activity, attachments), cycles with burndown, modules, estimates, List / Kanban / Spreadsheet
layouts, saved views, intake triage, analytics and an inbox. Vue 3 + frappe-ui frontend at `/runway`.

```bash
bench get-app runway && bench --site <site> install-app runway
cd apps/runway && yarn install && yarn build
```

See [FEATURES.md](FEATURES.md) for the full feature guide.

Users need the **Runway User** role and workspace membership (invite from Workspace settings).

#### License

agpl-3.0
