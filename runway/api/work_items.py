import frappe
from frappe import _
from frappe.utils import cint

from runway.utils import (
	INVERSE_RELATIONS,
	check_project_access,
	get_project_roles,
	get_workspace_roles,
	log_activity,
	parse_json,
	subscribe,
)

ITEM_FIELDS = [
	"name",
	"project",
	"sequence_id",
	"title",
	"state",
	"state_group",
	"priority",
	"start_date",
	"due_date",
	"estimate_point",
	"cycle",
	"parent_item",
	"sort_order",
	"is_draft",
	"archived_at",
	"completed_at",
	"owner",
	"creation",
	"modified",
]
PRIORITY_ORDER = {"Urgent": 0, "High": 1, "Medium": 2, "Low": 3, "None": 4}
ORDERABLE = {"sort_order", "creation", "modified", "start_date", "due_date", "priority", "sequence_id", "title"}
UPDATABLE = {
	"title",
	"description",
	"state",
	"priority",
	"start_date",
	"due_date",
	"estimate_point",
	"cycle",
	"parent_item",
	"sort_order",
	"is_draft",
	"assignees",
	"labels",
	"modules",
}
TABLES = {"assignees": "user", "labels": "label", "modules": "module"}
CHILD_DOCTYPES = {
	"assignees": "Runway Work Item Assignee",
	"labels": "Runway Work Item Label",
	"modules": "Runway Work Item Module",
}


# ---------------------------------------------------------------- queries


def _scope_projects(project=None, workspace=None) -> list[str]:
	roles = get_project_roles()
	if project:
		check_project_access(project)
		return [project]
	if workspace:
		if workspace not in get_workspace_roles():
			frappe.throw(_("Not permitted"), frappe.PermissionError)
		ws_projects = frappe.get_all(
			"Runway Project", filters={"workspace": workspace, "archived": 0}, pluck="name"
		)
		return [p for p in ws_projects if p in roles]
	return list(roles)


def query_items(
	project=None,
	workspace=None,
	filters=None,
	order_by="sort_order",
	include_triage=False,
	show_archived=False,
	show_drafts=False,
	show_sub_items=True,
	limit=5000,
):
	"""Lean work item rows with their multi-value fields attached.

	``filters`` keys: state, state_group, priority, assignees, labels, modules,
	cycle, owner, parent_item, search, due ("overdue"|"this_week"), mentions.
	Every list value means "any of".
	"""
	filters = parse_json(filters, {}) or {}
	projects = _scope_projects(project, workspace)
	if not projects:
		return []

	wi = frappe.qb.DocType("Runway Work Item")
	q = frappe.qb.from_(wi).select(*[wi[f] for f in ITEM_FIELDS]).where(wi.project.isin(projects))

	if not include_triage:
		q = q.where(wi.state_group != "Triage")
	if not cint(show_archived):
		q = q.where(wi.archived_at.isnull())
	if not cint(show_drafts):
		q = q.where(wi.is_draft == 0)
	if not cint(show_sub_items):
		q = q.where(wi.parent_item.isnull() | (wi.parent_item == ""))

	for field in ("state", "state_group", "priority", "owner"):
		if filters.get(field):
			q = q.where(wi[field].isin(_as_list(filters[field])))

	if "cycle" in filters and filters["cycle"] is not None:
		values = _as_list(filters["cycle"])
		cond = wi.cycle.isin([v for v in values if v] or [""])
		if None in values or "" in values:
			cond = cond | wi.cycle.isnull()
		q = q.where(cond)
	if filters.get("parent_item"):
		q = q.where(wi.parent_item == filters["parent_item"])
	if filters.get("search"):
		term = f"%{filters['search']}%"
		q = q.where(wi.title.like(term) | wi.name.like(term))
	if filters.get("due") == "overdue":
		q = q.where(wi.due_date < frappe.utils.nowdate()).where(wi.state_group.notin(["Completed", "Cancelled"]))
	for field in ("start_date", "due_date"):
		frm, to = (_as_list(filters.get(field)) + [None, None])[:2]
		if frm:
			q = q.where(wi[field] >= frm)
		if to:
			q = q.where(wi[field] <= to)

	for table, field in TABLES.items():
		if filters.get(table):
			child = frappe.qb.DocType(CHILD_DOCTYPES[table])
			sub = (
				frappe.qb.from_(child)
				.select(child.parent)
				.where(child.parenttype == "Runway Work Item")
				.where(child[field].isin(_as_list(filters[table])))
			)
			q = q.where(wi.name.isin(sub))
	if filters.get("subscribed_by"):
		sub_t = frappe.qb.DocType("Runway Subscription")
		q = q.where(
			wi.name.isin(frappe.qb.from_(sub_t).select(sub_t.work_item).where(sub_t.user == filters["subscribed_by"]))
		)

	rows = q.limit(cint(limit) or 5000).run(as_dict=True)
	_attach_children(rows)
	return _sort(rows, order_by)


def _as_list(v):
	if v is None:
		return []
	return v if isinstance(v, list) else [v]


def _sort(rows, order_by):
	order_by = order_by or "sort_order"
	desc = order_by.startswith("-")
	key = order_by.lstrip("-")
	if key not in ORDERABLE:
		key = "sort_order"
	if key == "priority":
		fn = lambda r: PRIORITY_ORDER.get(r.priority, 9)  # noqa: E731
	elif key in ("start_date", "due_date"):
		# Undated items sink to the bottom either way.
		fn = lambda r: (r.get(key) is None, str(r.get(key) or ""))  # noqa: E731
	else:
		fn = lambda r: (r.get(key) is None, r.get(key) or 0)  # noqa: E731
	return sorted(rows, key=fn, reverse=desc)


def _attach_children(rows):
	if not rows:
		return
	by_name = {r.name: r for r in rows}
	names = list(by_name)
	for r in rows:
		r.assignees, r.labels, r.modules = [], [], []
		r.sub_items_count = 0
		r.sub_items_done = 0
		r.link_count = 0
		r.attachment_count = 0
	for doctype, table, field in (
		("Runway Work Item Assignee", "assignees", "user"),
		("Runway Work Item Label", "labels", "label"),
		("Runway Work Item Module", "modules", "module"),
	):
		for c in frappe.get_all(
			doctype,
			filters={"parenttype": "Runway Work Item", "parent": ("in", names)},
			fields=["parent", field],
			order_by="idx asc",
		):
			by_name[c.parent][table].append(c[field])
	for c in frappe.db.sql(
		"""select parent_item, count(*) total,
			sum(state_group in ('Completed', 'Cancelled')) done
		from `tabRunway Work Item` where parent_item in %(names)s and archived_at is null
		group by parent_item""",
		{"names": names},
		as_dict=True,
	):
		by_name[c.parent_item].sub_items_count = c.total
		by_name[c.parent_item].sub_items_done = cint(c.done)
	for c in frappe.db.sql(
		"""select work_item, count(*) n from `tabRunway Work Item Link`
		where work_item in %(names)s group by work_item""",
		{"names": names},
		as_dict=True,
	):
		by_name[c.work_item].link_count = c.n
	for c in frappe.db.sql(
		"""select attached_to_name, count(*) n from `tabFile`
		where attached_to_doctype = 'Runway Work Item' and attached_to_name in %(names)s
		group by attached_to_name""",
		{"names": names},
		as_dict=True,
	):
		by_name[c.attached_to_name].attachment_count = c.n


@frappe.whitelist()
def get_items(
	project: str | None = None,
	workspace: str | None = None,
	filters: dict | str | None = None,
	order_by: str = "sort_order",
	show_archived: int = 0,
	show_sub_items: int = 1,
	show_drafts: int = 0,
	cycle: str | None = None,
	module: str | None = None,
	view: str | None = None,
):
	filters = parse_json(filters, {}) or {}
	if view:
		v = frappe.get_doc("Runway View", view)
		v.check_permission("read")
		filters = {**(parse_json(v.filters, {}) or {}), **filters}
		project = project or v.project
		workspace = workspace or v.workspace
	if cycle:
		filters["cycle"] = [cycle]
	if module:
		filters["modules"] = [module]
	return query_items(
		project=project,
		workspace=workspace,
		filters=filters,
		order_by=order_by,
		show_archived=show_archived,
		show_sub_items=show_sub_items,
		show_drafts=show_drafts,
	)


def get_row(name: str):
	rows = frappe.get_all("Runway Work Item", filters={"name": name}, fields=ITEM_FIELDS)
	_attach_children(rows)
	return rows[0] if rows else None


# ---------------------------------------------------------------- mutations


def _apply(doc, values: dict):
	for key, value in values.items():
		if key not in UPDATABLE:
			frappe.throw(_("Field {0} cannot be updated here").format(key))
		if key in TABLES:
			field = TABLES[key]
			doc.set(key, [{field: v} for v in (parse_json(value, []) or []) if v])
		else:
			doc.set(key, value if value != "" else None)


@frappe.whitelist()
def create_item(project: str, values: dict | str | None = None):
	check_project_access(project, write=True)
	values = parse_json(values, {}) or {}
	doc = frappe.new_doc("Runway Work Item")
	doc.project = project
	_apply(doc, values)
	if not doc.assignees:
		default_assignee = frappe.db.get_value("Runway Project", project, "default_assignee")
		if default_assignee:
			doc.append("assignees", {"user": default_assignee})
	doc.insert()
	return get_row(doc.name)


@frappe.whitelist()
def update_item(name: str, values: dict | str):
	doc = frappe.get_doc("Runway Work Item", name)
	doc.check_permission("write")
	_apply(doc, parse_json(values, {}) or {})
	doc.save()
	return get_row(name)


@frappe.whitelist()
def bulk_update(names: list | str, values: dict | str):
	names = parse_json(names, [])
	values = parse_json(values, {})
	for name in names:
		update_item(name, values)
	return [get_row(n) for n in names]


@frappe.whitelist()
def archive(name: str, restore: int = 0):
	doc = frappe.get_doc("Runway Work Item", name)
	doc.check_permission("write")
	if not cint(restore) and doc.state_group not in ("Completed", "Cancelled"):
		frappe.throw(_("Only completed or cancelled work items can be archived"))
	doc.archived_at = None if cint(restore) else frappe.utils.now_datetime()
	doc.save()
	return get_row(name)


@frappe.whitelist()
def delete_item(name: str):
	doc = frappe.get_doc("Runway Work Item", name)
	doc.check_permission("delete")
	frappe.delete_doc("Runway Work Item", name)


# ---------------------------------------------------------------- detail


@frappe.whitelist()
def get_detail(name: str):
	doc = frappe.get_doc("Runway Work Item", name)
	doc.check_permission("read")
	user = frappe.session.user
	item = get_row(name)
	item.description = doc.description

	item.parent = get_row(doc.parent_item) if doc.parent_item else None
	sub_names = frappe.get_all(
		"Runway Work Item", filters={"parent_item": name}, pluck="name", order_by="sort_order asc"
	)
	item.sub_items = query_items(project=doc.project, filters={"parent_item": name}, show_archived=1) if sub_names else []

	item.relations = get_relations(name)
	item.links = frappe.get_all(
		"Runway Work Item Link",
		filters={"work_item": name},
		fields=["name", "title", "url", "owner", "creation"],
		order_by="creation asc",
	)
	item.attachments = frappe.get_all(
		"File",
		filters={"attached_to_doctype": "Runway Work Item", "attached_to_name": name},
		fields=["name", "file_name", "file_url", "file_size", "owner", "creation", "is_private"],
		order_by="creation asc",
	)
	item.is_subscribed = bool(frappe.db.exists("Runway Subscription", {"work_item": name, "user": user}))
	item.intake = frappe.db.get_value(
		"Runway Intake Item", {"work_item": name}, ["name", "status", "snoozed_till", "duplicate_of"], as_dict=True
	)
	item.timeline = get_timeline(name)
	item.can_edit = doc.has_permission("write")
	return item


def get_relations(name: str):
	out = []
	for r in frappe.get_all(
		"Runway Work Item Relation",
		filters={"work_item": name},
		fields=["name", "related_item", "relation_type"],
	):
		out.append({"name": r.name, "relation_type": r.relation_type, "item": r.related_item})
	for r in frappe.get_all(
		"Runway Work Item Relation",
		filters={"related_item": name},
		fields=["name", "work_item", "relation_type"],
	):
		out.append({"name": r.name, "relation_type": INVERSE_RELATIONS[r.relation_type], "item": r.work_item})
	rows = {
		x.name: x
		for x in frappe.get_all(
			"Runway Work Item",
			filters={"name": ("in", [o["item"] for o in out] or [""])},
			fields=["name", "title", "state", "state_group", "project", "priority"],
		)
	}
	return [{**o, **{"detail": rows.get(o["item"])}} for o in out if o["item"] in rows]


def get_timeline(name: str):
	activity = frappe.get_all(
		"Runway Activity",
		filters={"work_item": name},
		fields=["name", "actor", "verb", "field", "old_value", "new_value", "creation"],
		order_by="creation asc",
	)
	for a in activity:
		a.kind = "activity"
	comments = frappe.get_all(
		"Runway Comment",
		filters={"work_item": name},
		fields=["name", "owner", "content", "access", "edited_at", "creation"],
		order_by="creation asc",
	)
	reactions = frappe.get_all(
		"Runway Reaction",
		filters={"reference_doctype": "Runway Comment", "reference_name": ("in", [c.name for c in comments] or [""])},
		fields=["reference_name", "emoji", "user"],
	)
	for c in comments:
		c.kind = "comment"
		c.reactions = [r for r in reactions if r.reference_name == c.name]
	return sorted(activity + comments, key=lambda x: x.creation)


# ---------------------------------------------------------------- sub-resources


@frappe.whitelist()
def add_relation(work_item: str, related_item: str, relation_type: str):
	frappe.get_doc("Runway Work Item", work_item).check_permission("write")
	frappe.get_doc("Runway Work Item", related_item).check_permission("read")
	# Store inverse kinds ("blocking", "implements", ...) as the canonical direction.
	canonical = {v: k for k, v in INVERSE_RELATIONS.items() if k != v}
	if relation_type in canonical:
		work_item, related_item, relation_type = related_item, work_item, canonical[relation_type]
	frappe.get_doc(
		{
			"doctype": "Runway Work Item Relation",
			"work_item": work_item,
			"related_item": related_item,
			"relation_type": relation_type,
		}
	).insert(ignore_permissions=True)


@frappe.whitelist()
def remove_relation(name: str):
	rel = frappe.get_doc("Runway Work Item Relation", name)
	frappe.get_doc("Runway Work Item", rel.work_item).check_permission("write")
	rel.delete(ignore_permissions=True)


@frappe.whitelist()
def add_link(work_item: str, url: str, title: str | None = None):
	frappe.get_doc("Runway Work Item", work_item).check_permission("write")
	frappe.get_doc(
		{"doctype": "Runway Work Item Link", "work_item": work_item, "url": url, "title": title}
	).insert(ignore_permissions=True)


@frappe.whitelist()
def remove_link(name: str):
	link = frappe.get_doc("Runway Work Item Link", name)
	frappe.get_doc("Runway Work Item", link.work_item).check_permission("write")
	log_activity(link.work_item, "removed_link", "link", link.url, None)
	link.delete(ignore_permissions=True)


@frappe.whitelist()
def remove_attachment(file_name: str):
	f = frappe.get_doc("File", file_name)
	if f.attached_to_doctype != "Runway Work Item":
		frappe.throw(_("Not a work item attachment"))
	frappe.get_doc("Runway Work Item", f.attached_to_name).check_permission("write")
	log_activity(f.attached_to_name, "removed_attachment", "attachment", f.file_name, None)
	f.delete(ignore_permissions=True)


@frappe.whitelist()
def toggle_subscription(work_item: str):
	frappe.get_doc("Runway Work Item", work_item).check_permission("read")
	user = frappe.session.user
	name = frappe.db.get_value("Runway Subscription", {"work_item": work_item, "user": user})
	if name:
		frappe.delete_doc("Runway Subscription", name, ignore_permissions=True)
		return False
	subscribe(work_item, user)
	return True


@frappe.whitelist()
def add_comment(work_item: str, content: str, access: str = "Internal"):
	frappe.get_doc("Runway Work Item", work_item).check_permission("read")
	doc = frappe.get_doc(
		{"doctype": "Runway Comment", "work_item": work_item, "content": content, "access": access}
	)
	doc.insert()
	return doc.name


@frappe.whitelist()
def update_comment(name: str, content: str):
	doc = frappe.get_doc("Runway Comment", name)
	doc.content = content
	doc.save()


@frappe.whitelist()
def delete_comment(name: str):
	frappe.delete_doc("Runway Comment", name)


@frappe.whitelist()
def toggle_reaction(reference_doctype: str, reference_name: str, emoji: str):
	if reference_doctype != "Runway Comment":
		frappe.throw(_("Reactions are only supported on comments"))
	frappe.get_doc(reference_doctype, reference_name).check_permission("read")
	user = frappe.session.user
	key = {"reference_doctype": reference_doctype, "reference_name": reference_name, "user": user, "emoji": emoji}
	name = frappe.db.get_value("Runway Reaction", key)
	if name:
		frappe.delete_doc("Runway Reaction", name, ignore_permissions=True)
		return False
	frappe.get_doc({"doctype": "Runway Reaction", **key}).insert(ignore_permissions=True)
	return True


@frappe.whitelist()
def search_items(query: str, workspace: str | None = None, project: str | None = None, limit: int = 20):
	return query_items(
		project=project,
		workspace=workspace,
		filters={"search": query},
		order_by="-modified",
		limit=cint(limit) or 20,
	)


@frappe.whitelist()
def get_versions(name: str):
	"""Description history (WI-10) from Frappe's Version log."""
	frappe.get_doc("Runway Work Item", name).check_permission("read")
	out = []
	for v in frappe.get_all(
		"Version",
		filters={"ref_doctype": "Runway Work Item", "docname": name},
		fields=["owner", "creation", "data"],
		order_by="creation desc",
	):
		data = frappe.parse_json(v.data) or {}
		for field, old, new in data.get("changed", []):
			if field == "description":
				out.append({"owner": v.owner, "creation": v.creation, "old": old, "new": new})
	return out
