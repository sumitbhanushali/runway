# Runway — Feature Guide

Runway is a Plane-style project management app for Frappe, served at `/runway`. This guide covers what
the current build (Core MVP) does, how it maps to the requirements in `plane_spec.md`, and what is not
built yet.

## Contents

1. [Concepts](#concepts)
2. [Workspaces and members](#workspaces-and-members)
3. [Projects](#projects)
4. [Work items](#work-items)
5. [States and workflow](#states-and-workflow)
6. [Layouts, filters and display](#layouts-filters-and-display)
7. [Saved views](#saved-views)
8. [Cycles](#cycles)
9. [Modules](#modules)
10. [Estimates](#estimates)
11. [Intake](#intake)
12. [Analytics](#analytics)
13. [Home, your work and inbox](#home-your-work-and-inbox)
14. [Navigation and shortcuts](#navigation-and-shortcuts)
15. [Roles and permissions](#roles-and-permissions)
16. [Spec coverage](#spec-coverage)
17. [Not yet built](#not-yet-built)

---

## Concepts

```
Workspace
 ├── Members (Admin / Member / Guest)
 ├── Saved views (workspace level)
 └── Projects
      ├── Members (Admin / Member / Guest)
      ├── States (each in a fixed group), Labels, Estimate
      ├── Work items  ── can sit in one Cycle and several Modules at once
      ├── Cycles      ── slice work by time
      ├── Modules     ── slice work by feature / epic
      ├── Views       ── slice work by saved filter
      └── Intake      ── triage queue feeding the backlog
```

URLs follow the same shape: `/runway/<workspace>/projects/<PROJECT>/work-items`,
`/runway/<workspace>/browse/WEB-142`, and so on.

## Workspaces and members

- **Create a workspace** with a name and URL slug. New users with no workspace are sent to onboarding.
- **Switch workspaces** from the menu at the top of the sidebar.
- **Invite by email** (Workspace settings → Members). Unknown emails get a new user account with a
  welcome email and the *Runway User* role.
- **Workspace roles:** Admin, Member, Guest. Admins can change roles and remove members; removing a
  member also removes them from the workspace's projects.
- Every workspace must keep at least one Admin.

## Projects

- **Create a project** with a name, icon (emoji), description and an **identifier** (up to 12 letters or
  digits, e.g. `WEB`). The identifier is suggested from the name and cannot be changed later.
- **Access:** *Public* projects are visible to every non-guest workspace member and can be joined from the
  Projects page. *Secret* projects are visible only to people added to them.
- **Defaults seeded on create:** states Backlog, Todo, In Progress, Done, Cancelled (plus a hidden Triage
  state) and labels Bug, Feature, Improvement. The creator becomes the project Admin.
- **Project settings** (Admins only):
  - *General* — name, icon, description, access, lead, default assignee, archive / restore.
  - *Members* — add workspace members with a role, change roles, remove.
  - *Features* — turn Cycles, Modules, Views and Intake on or off per project.
  - *States*, *Labels*, *Estimates* — see the sections below.
- **Favorites:** star a project to pin it in the sidebar.
- A project with work items cannot be deleted. Archive it instead.

## Work items

**Fields:** title, rich-text description, state, priority (Urgent, High, Medium, Low, None),
assignees, labels, start date, due date, estimate, cycle, modules, parent.

- **Numbering:** each item gets a per-project ID such as `WEB-142`, allocated safely under concurrent
  creation.
- **Create** from the "Work item" button, the sidebar, `C` on the keyboard, or the inline
  "New work item" row at the bottom of any group. Items created inside a group, cycle or module start
  with that group's values. "Create more" keeps the dialog open for quick entry.
- **Peek panel:** clicking an item opens it in a side panel without leaving the list (`?peek=WEB-12` in
  the URL). The expand button opens the full page.
- **Inline editing:** state, priority, assignees, labels, dates, estimate, cycle and modules can be
  changed from list rows, board cards, spreadsheet cells and the detail view. Changes appear immediately
  and roll back with an error message if the server rejects them.
- **Sub-work items:** create children inline or attach existing items. The parent shows a
  "done / total" roll-up. Parents must be in the same project, and circular parent chains are rejected.
- **Relations:** blocked by / blocking, relates to, duplicate of, starts before / after,
  finishes before / after, implemented by / implements. Each relation shows from both sides.
- **Links and attachments:** add URLs with titles; upload files (stored as private Frappe files).
- **Comments:** rich text with @mentions of project members, emoji reactions, edit (marked "edited")
  and delete for the author, and *Internal* or *External* visibility tags.
- **Activity log:** every change to tracked fields is recorded with who, what and when, and shown in a
  timeline with comments. Filter the timeline to All, Comments or Updates.
- **Description history:** previous versions are kept through Frappe's version log.
- **Subscriptions:** creators, assignees and commenters are subscribed automatically. Anyone can
  subscribe or unsubscribe from the item menu.
- **Archive** completed or cancelled items (and restore them); **delete** removes the item with its
  comments, activity and relations.
- **Copy link** from the item menu.

## States and workflow

- Each project defines its own states. Every state belongs to one fixed **group**: Backlog, Unstarted,
  Started, Completed, Cancelled (and Triage, used only by Intake).
- Progress bars, burndowns and analytics use the group, so renaming or adding states never breaks
  reporting.
- In settings you can add states to any group, rename them, change colors and pick the default state
  for new items.
- Moving an item into a Completed state records its completion time (used by burndowns); moving it out
  clears it.
- The default state, the Triage state, and states that still hold work items cannot be deleted.

## Layouts, filters and display

Every list of work items (project, cycle, module, view, your work) shares the same toolbar.

| Layout | What it does |
| --- | --- |
| **List** | Grouped, collapsible rows with inline properties and an add row per group. |
| **Kanban** | One column per group. Drag cards between columns to change the grouped field, or within a column to reorder. |
| **Spreadsheet** | A flat table with one editable column per property and a sticky title column. |

- **Search** by title or ID.
- **Filters:** state (or state group across projects), priority, assignees, labels, cycle (including
  "no cycle"), modules, created by, and overdue. Active filters show as removable chips.
- **Display:** group by state, state group, priority, assignee, label, cycle, module or none; order by
  manual, created, updated, start date, due date or priority; show or hide sub-work items and empty
  groups; choose which properties show on rows and cards.
- Filter and display choices are remembered per list in the browser.

## Saved views

- **Save view** stores the current filters, layout, grouping, ordering and visible properties under a
  name, as *Private* (only you) or *Public* (everyone who can see the project).
- **Project views** live under the project's Views tab; **workspace views** span all projects.
- **Built-in workspace views:** All work items, Assigned to me, Created by me, Subscribed.
- When you change a saved view, **Reset** returns it to the saved version and **Update view** saves the
  changes (owner only).

## Cycles

- Create a cycle with a title, description, start date and end date. Without dates it stays a *Draft*.
- **No overlaps:** cycles in the same project cannot share dates, so only one can be active at a time.
- **Status** is worked out from the dates: Draft, Upcoming, Current or Completed. A daily job keeps it
  up to date.
- The **cycles page** groups cycles by status, with a progress bar, done count and days left for the
  current cycle.
- The **cycle page** shows the cycle's work items (Kanban by default) and a progress panel with counts
  per state group and a **burndown chart** (ideal line against remaining work), by item count or estimate
  points.
- **Complete cycle** freezes a snapshot of progress and the burndown, and can move unfinished items to
  another open cycle. Completed cycles cannot be rescheduled or receive new items.

## Modules

- Feature- or epic-level groupings that can span cycles. Fields: title, description, status (Backlog,
  Planned, In Progress, Paused, Completed, Cancelled), lead, start date, target date.
- A work item can belong to several modules.
- The modules page shows cards with progress and the target date. The module page shows its work items
  and a details panel with progress per state group.

## Estimates

- Each project can use **Points** (numbers, e.g. Fibonacci 1, 2, 3, 5, 8, 13) or **Categories** (e.g.
  T-shirt sizes XS–XL). Presets are provided.
- Estimates appear as a property on work items and feed cycle burndowns, module progress and analytics.
- For categories, each value counts by its position in the list (XS = 1, S = 2, ...).
- Saving an empty list turns estimates off.

## Intake

Turn Intake on under Project settings → Features.

- **Submit a request** with a title, details and priority. Members and Guests can submit.
- New requests are created in the hidden **Triage** state and do not appear in normal lists or views.
- Project Admins are notified of new requests.
- **Reviewers** (project Admins and Members) open a request and can:
  - **Accept** — moves it to the project's default state (the backlog).
  - **Decline** — moves it to a Cancelled state.
  - **Snooze** — for 1 day, 3 days or a week, or unsnooze.
  - **Mark duplicate** — links it to the existing item and closes it.
- The submitter is notified of the outcome. Open and Closed tabs separate pending from finished
  requests.

## Analytics

- Scope: all projects in the workspace, or a single project.
- **X-axis:** state group, state, priority, assignee, label, cycle, module, created by, due month.
- **Y-axis:** work item count or estimate points.
- **Segment by** any second dimension to get stacked bars.
- Summary cards show counts per state group. A table under the chart shows the same numbers.
- **Export CSV** downloads the work items in scope, one row each.

## Home, your work and inbox

- **Home:** greeting, counts for items assigned to you (open, overdue, due this week, completed),
  upcoming due dates and recently visited items.
- **Your work:** Assigned, Created and Subscribed tabs, each with the full layout and filter toolbar.
- **Inbox:** notifications for assignments, mentions, state changes, comments, updates and intake
  outcomes.
  - All, Unread, Snoozed and Archived tabs.
  - Mark read or unread, mark all read, archive or unarchive, snooze (1 hour, tomorrow, next week).
  - Opening a notification marks it read and opens the work item.
  - The unread count shows in the sidebar and updates live when the realtime server is running.

## Navigation and shortcuts

- **Sidebar:** workspace switcher, Home, Inbox, Your work, Views, Analytics, Projects, favorites, and a
  project tree with each project's sections. User menu: theme (light / dark / system), Desk (for system
  managers), log out.
- **Project tabs** in the header: Work items, Cycles, Modules, Views, Intake, Settings (as enabled).

| Shortcut | Action |
| --- | --- |
| `⌘K` / `Ctrl+K` | Search work items and projects, and run actions |
| `C` | Create a work item |
| `Esc` | Close the peek panel |
| `⌘Enter` / `Ctrl+Enter` | Post a comment / create from the dialog |

## Roles and permissions

Users need the **Runway User** role (given automatically on invite). **Runway Admin** and **System
Manager** can see everything.

| Who | Can do |
| --- | --- |
| Workspace Admin | Manage workspace members and roles; create projects; everything a Member can. |
| Workspace Member | See and join Public projects; create projects. |
| Workspace Guest | See only projects they are added to. |
| Project Admin | Edit project settings, members, states, estimates and feature toggles; triage intake; full work item access. |
| Project Member | Create and edit work items, cycles, modules and views; triage intake. |
| Project Guest | Read-only on work items; can comment, react, subscribe and submit intake requests. |

- Access is enforced on the server for every list and record, not only hidden in the UI.
- Comments can be edited or deleted by their author or a project Admin.
- Notifications, favorites and recent visits are private to each user. Private views are visible only
  to their owner.

## Spec coverage

How the build maps to the functional requirements in `plane_spec.md`.

| Spec item | Status | Notes |
| --- | --- | --- |
| WI-1 Create work item with all core fields | Done | |
| WI-2 Per-project numbering (`WEB-142`) | Done | Locked sequence, safe under concurrency |
| WI-3 Sub-work items with progress roll-up | Done | |
| WI-4 Relations | Done | All seven pairs, shown from both sides |
| WI-5 Comments, mentions, reactions, edit, internal / external | Partial | Edits are marked, but comment edit history isn't kept |
| WI-6 Attachments and links | Done | |
| WI-7 Activity log of field changes | Done | |
| WI-8 Subscribe and notify | Done | In-app; email notifications not built |
| WI-9 Drafts, archive, soft delete with restore | Partial | Archive / restore done; drafts are stored but have no UI; delete is permanent |
| WI-10 Description version history | Partial | Stored in Frappe versions (API exists); no history viewer in the UI |
| States and groups, default states | Done | |
| Cycles: dates, no overlap, burndown, transfer, snapshot | Done | Owner and timezone fields not exposed |
| Modules: lead, dates, status, progress | Done | Members and links are in the data model but not editable in the UI |
| Estimates: categories or points | Done | |
| Layouts: List, Kanban, Spreadsheet | Done | |
| Layouts: Calendar, Gantt | Not built | |
| Filter, group, sort, display properties | Done | Sub-grouping not built |
| Saved views (project and workspace, public / private) | Done | Plus the four built-in workspace views |
| Intake triage | Done | No external form or email intake |
| Analytics with custom axes and CSV export | Done | |
| Personal home, recent items | Done | Stickies and quick links not built |
| Inbox: read / unread, snooze, archive | Done | |
| Roles, invite by email, public / secret projects | Done | |

## Not yet built

These are left for later builds, following the plan:

- Pages (collaborative documents) and real-time co-editing
- Calendar and Gantt layouts, sub-grouping
- Publishing boards to a public URL
- Public REST API tokens, webhooks, importers (GitHub, Jira) and JSON / XLSX exports
- Email notifications
- SSO / OAuth sign-in and the instance admin ("God mode") screens
- Stickies, quick links and comment edit history
- Full translation of UI strings and custom themes
