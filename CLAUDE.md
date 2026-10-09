# CLAUDE.md

Runway is a Plane-style project management app for Frappe (spec: `../../plane_spec.md`).
Python backend in `runway/`, Vue 3 + TypeScript + frappe-ui frontend in `frontend/`, served at `/runway`.
User-facing features are documented in `FEATURES.md`; keep it in step when behaviour changes.

## Commands

```bash
yarn dev                         # Vite dev server on :8080, proxies to bench
yarn build                       # -> runway/public/frontend + runway/www/runway.html
cd frontend && yarn lint         # eslint + prettier --check
cd frontend && yarn typecheck    # vue-tsc
bench --site mf.sbm16 run-tests --app runway
```

## Backend layout

- `runway/runway/doctype/` — all DocTypes (module "Runway"). Work items are named `{PROJECT}-{seq}`; the
  sequence is allocated under a row lock on `Runway Project.item_sequence`.
- `runway/permissions.py` — row-level access from workspace + project membership. `frappe.get_all`
  bypasses it; `get_list` / `get_doc().check_permission` apply it.
- `runway/utils.py` — access cache (`get_project_roles`, cleared on membership changes), activity log,
  notifications, subscriptions.
- `runway/api/*.py` — whitelisted endpoints the frontend calls (`boot`, `work_items`, `cycles`, `modules`,
  `intake`, `analytics`, `notifications`, `my_work`). Simple CRUD (cycles, modules, views, states, labels)
  goes through `frappe.client.*`.
- State *groups* (Backlog/Unstarted/Started/Completed/Cancelled/Triage) drive all reporting; work items
  denormalize `state_group`.

## Frontend conventions

- Use frappe-ui components and tokens (`ink-*`, `surface-*`, `outline-*`); icons are `lucide-*` classes.
- `src/api.ts` wraps every backend call; `src/stores/workspace.ts` holds boot data (projects with states,
  labels, members, cycles, modules).
- `WorkItemsBoard` renders any scope (project / cycle / module / view / my work) in List, Kanban or
  Spreadsheet; `useDisplay` persists filters + layout per scope.
- Cross-component updates go through `utils/bus.ts` (`item-updated`, `item-created`, `create-item`...).
- The peek panel opens via the `?peek=WEB-12` query param.
