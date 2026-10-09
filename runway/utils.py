import re

import frappe
from frappe.utils import now_datetime

ADMIN_ROLES = {"System Manager", "Runway Admin"}
STATE_GROUPS = ["Backlog", "Unstarted", "Started", "Completed", "Cancelled", "Triage"]
DONE_GROUPS = {"Completed", "Cancelled"}

DEFAULT_STATES = [
	# title, group, color, is_default
	("Backlog", "Backlog", "#a3a3a3", 1),
	("Todo", "Unstarted", "#3a3a3a", 0),
	("In Progress", "Started", "#f59e0b", 0),
	("Done", "Completed", "#16a34a", 0),
	("Cancelled", "Cancelled", "#9ca3af", 0),
	("Triage", "Triage", "#4e5355", 0),
]
DEFAULT_LABELS = [("Bug", "#ef4444"), ("Feature", "#3b82f6"), ("Improvement", "#8b5cf6")]

INVERSE_RELATIONS = {
	"blocked_by": "blocking",
	"relates_to": "relates_to",
	"duplicate": "duplicate",
	"start_before": "start_after",
	"finish_before": "finish_after",
	"implemented_by": "implements",
}


def is_runway_admin(user: str | None = None) -> bool:
	user = user or frappe.session.user
	if user == "Administrator":
		return True
	return bool(ADMIN_ROLES.intersection(frappe.get_roles(user)))


def _cache(key: str, user: str, fn):
	store = getattr(frappe.local, "runway_cache", None)
	if store is None:
		store = frappe.local.runway_cache = {}
	k = (key, user)
	if k not in store:
		store[k] = fn()
	return store[k]


def clear_access_cache():
	frappe.local.runway_cache = {}


def get_workspace_roles(user: str | None = None) -> dict[str, str]:
	"""{workspace: role} for every workspace the user belongs to."""
	user = user or frappe.session.user

	def load():
		if is_runway_admin(user):
			return {w: "Admin" for w in frappe.get_all("Runway Workspace", pluck="name")}
		rows = frappe.get_all(
			"Runway Workspace Member", filters={"user": user}, fields=["workspace", "role"]
		)
		return {r.workspace: r.role for r in rows}

	return _cache("workspaces", user, load)


def get_project_roles(user: str | None = None) -> dict[str, str]:
	"""{project: role} for every project the user can see.

	Explicit project membership wins; otherwise Public projects inherit the
	user's workspace role (Guests only see projects they are added to).
	"""
	user = user or frappe.session.user

	def load():
		projects = frappe.get_all("Runway Project", fields=["name", "workspace", "network"])
		if is_runway_admin(user):
			return {p.name: "Admin" for p in projects}
		ws_roles = get_workspace_roles(user)
		explicit = {
			r.project: r.role
			for r in frappe.get_all(
				"Runway Project Member", filters={"user": user}, fields=["project", "role"]
			)
		}
		roles = {}
		for p in projects:
			if p.workspace not in ws_roles:
				continue
			if p.name in explicit:
				roles[p.name] = explicit[p.name]
			elif p.network == "Public" and ws_roles[p.workspace] != "Guest":
				roles[p.name] = ws_roles[p.workspace]
		return roles

	return _cache("projects", user, load)


def get_project_role(project: str, user: str | None = None) -> str | None:
	return get_project_roles(user).get(project)


def check_project_access(project: str, write: bool = False):
	role = get_project_role(project)
	if not role or (write and role == "Guest"):
		frappe.throw(frappe._("Not permitted for project {0}").format(project), frappe.PermissionError)
	return role


def check_project_admin(project: str):
	if get_project_role(project) != "Admin":
		frappe.throw(frappe._("Only project admins can do this"), frappe.PermissionError)


def check_workspace_access(workspace: str, admin: bool = False):
	role = get_workspace_roles().get(workspace)
	if not role or (admin and role != "Admin"):
		frappe.throw(frappe._("Not permitted for workspace {0}").format(workspace), frappe.PermissionError)
	return role


def parse_json(value, default=None):
	if value is None or value == "":
		return default
	if isinstance(value, str):
		return frappe.parse_json(value)
	return value


MENTION_RE = re.compile(r'data-type="mention"[^>]*data-id="([^"]+)"|data-id="([^"]+)"[^>]*data-type="mention"')


def extract_mentions(html: str | None) -> set[str]:
	if not html:
		return set()
	return {a or b for a, b in MENTION_RE.findall(html)}


def subscribe(work_item: str, user: str):
	if user in (None, "Guest"):
		return
	if not frappe.db.exists("Runway Subscription", {"work_item": work_item, "user": user}):
		frappe.get_doc({"doctype": "Runway Subscription", "work_item": work_item, "user": user}).insert(
			ignore_permissions=True
		)


def get_subscribers(work_item: str) -> list[str]:
	return frappe.get_all("Runway Subscription", filters={"work_item": work_item}, pluck="user")


def notify(users, work_item: str | None, notification_type: str, message: str, actor: str | None = None):
	actor = actor or frappe.session.user
	for user in set(users or []):
		if not user or user == actor or user == "Guest":
			continue
		frappe.get_doc(
			{
				"doctype": "Runway Notification",
				"for_user": user,
				"work_item": work_item,
				"actor": actor,
				"notification_type": notification_type,
				"message": message,
			}
		).insert(ignore_permissions=True)
		frappe.publish_realtime(
			"runway_notification",
			{"work_item": work_item, "type": notification_type},
			user=user,
			after_commit=True,
		)


def log_activity(work_item: str, verb: str, field=None, old_value=None, new_value=None, actor=None):
	frappe.get_doc(
		{
			"doctype": "Runway Activity",
			"work_item": work_item,
			"actor": actor or frappe.session.user,
			"verb": verb,
			"field": field,
			"old_value": None if old_value is None else str(old_value),
			"new_value": None if new_value is None else str(new_value),
		}
	).insert(ignore_permissions=True)


def estimate_value(point: str | None, points: list[str] | None = None) -> float:
	"""Numeric weight of an estimate point. Category estimates weigh by position (XS=1, S=2, ...)."""
	if not point:
		return 0
	try:
		return float(point)
	except ValueError:
		if points and point in points:
			return float(points.index(point) + 1)
		return 0


def now():
	return now_datetime()


def on_file_attached(doc, method=None):
	if doc.attached_to_doctype == "Runway Work Item" and doc.attached_to_name:
		log_activity(doc.attached_to_name, "added_attachment", "attachment", None, doc.file_name)
