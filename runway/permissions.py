"""Row-level access for Runway.

Access is derived from workspace + project membership (see ``runway.utils``):
every project-scoped record is visible when its project is, and records hanging
off a work item follow that work item's project.
"""

import frappe

from runway.utils import get_project_roles, get_workspace_roles, is_runway_admin

PROJECT_SCOPED = {
	"Runway Project": "name",
	"Runway Project Member": "project",
	"Runway State": "project",
	"Runway Label": "project",
	"Runway Estimate": "project",
	"Runway Cycle": "project",
	"Runway Module": "project",
	"Runway Work Item": "project",
	"Runway Intake Item": "project",
}
ITEM_SCOPED = {
	"Runway Comment",
	"Runway Activity",
	"Runway Work Item Relation",
	"Runway Work Item Link",
	"Runway Subscription",
}
USER_SCOPED = {
	"Runway Notification": "for_user",
	"Runway Favorite": "user",
	"Runway Recent Visit": "user",
}
# Guests may create these in projects they can see; everything else is read-only for them.
GUEST_WRITABLE = {"Runway Comment", "Runway Intake Item", "Runway Reaction", "Runway Subscription"}


def _in(values) -> str:
	values = list(values)
	if not values:
		return "('')"
	return "(" + ", ".join(frappe.db.escape(v) for v in values) + ")"


def _conditions(doctype: str, user: str | None) -> str:
	user = user or frappe.session.user
	if is_runway_admin(user):
		return ""
	table = f"`tab{doctype}`"
	if doctype == "Runway Workspace":
		return f"{table}.name in {_in(get_workspace_roles(user))}"
	if doctype == "Runway Workspace Member":
		return f"{table}.workspace in {_in(get_workspace_roles(user))}"
	if doctype in PROJECT_SCOPED:
		return f"{table}.`{PROJECT_SCOPED[doctype]}` in {_in(get_project_roles(user))}"
	if doctype in ITEM_SCOPED:
		return (
			f"{table}.work_item in (select wi.name from `tabRunway Work Item` wi"
			f" where wi.project in {_in(get_project_roles(user))})"
		)
	if doctype in USER_SCOPED:
		return f"{table}.`{USER_SCOPED[doctype]}` = {frappe.db.escape(user)}"
	if doctype == "Runway View":
		u = frappe.db.escape(user)
		return (
			f"({table}.owner = {u} or {table}.access = 'Public')"
			f" and {table}.workspace in {_in(get_workspace_roles(user))}"
			f" and ({table}.project is null or {table}.project = ''"
			f" or {table}.project in {_in(get_project_roles(user))})"
		)
	return ""


def query_conditions(user=None, doctype=None):
	return _conditions(doctype, user)


def _project_of(doc) -> str | None:
	if doc.doctype == "Runway Project":
		return doc.name
	if doc.doctype in PROJECT_SCOPED:
		return doc.get("project")
	if doc.doctype in ITEM_SCOPED and doc.get("work_item"):
		return frappe.db.get_value("Runway Work Item", doc.work_item, "project")
	return None


def has_permission(doc, ptype=None, user=None, debug=False):
	user = user or frappe.session.user
	if is_runway_admin(user):
		return True
	ptype = ptype or "read"
	read_only = ptype in ("read", "select", "print", "email", "report", "export")

	if doc.doctype == "Runway Workspace":
		if doc.is_new() and ptype == "create":
			return True
		role = get_workspace_roles(user).get(doc.name)
		return bool(role) and (read_only or role == "Admin")

	if doc.doctype == "Runway Workspace Member":
		role = get_workspace_roles(user).get(doc.workspace)
		return bool(role) and (read_only or role == "Admin")

	if doc.doctype in USER_SCOPED:
		return doc.get(USER_SCOPED[doc.doctype]) == user or doc.is_new()

	if doc.doctype == "Runway View":
		if not get_workspace_roles(user).get(doc.workspace):
			return False
		if doc.project and doc.project not in get_project_roles(user):
			return False
		return doc.owner == user or doc.is_new() or (read_only and doc.access == "Public")

	if doc.doctype == "Runway Reaction":
		return read_only or doc.user == user or doc.is_new()

	project = _project_of(doc)
	if not project:
		# A brand-new project has no membership yet; workspace members may create one.
		if doc.doctype == "Runway Project" and doc.is_new():
			return get_workspace_roles(user).get(doc.get("workspace")) in ("Admin", "Member")
		return True

	if doc.doctype == "Runway Project" and doc.is_new():
		return get_workspace_roles(user).get(doc.get("workspace")) in ("Admin", "Member")

	role = get_project_roles(user).get(project)
	if not role:
		return False
	if read_only:
		return True
	if role == "Guest":
		return doc.doctype in GUEST_WRITABLE and (doc.is_new() or doc.owner == user)
	# Project configuration is for project admins.
	if doc.doctype in ("Runway Project", "Runway Project Member", "Runway State", "Runway Estimate"):
		return role == "Admin"
	if doc.doctype == "Runway Comment" and not doc.is_new() and ptype in ("write", "delete"):
		return doc.owner == user or role == "Admin"
	return True
