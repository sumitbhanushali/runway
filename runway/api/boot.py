import frappe
from frappe import _

from runway.doctype_helpers import project_payload
from runway.utils import (
	check_project_access,
	check_project_admin,
	check_workspace_access,
	clear_access_cache,
	get_project_roles,
	get_workspace_roles,
	is_runway_admin,
)


@frappe.whitelist()
def get_boot(workspace: str | None = None):
	"""Everything the shell needs in one round trip."""
	user = frappe.session.user
	ws_roles = get_workspace_roles()
	workspaces = frappe.get_all(
		"Runway Workspace",
		filters={"name": ("in", list(ws_roles) or [""])},
		fields=["name", "title", "slug", "logo"],
		order_by="title asc",
	)
	for w in workspaces:
		w.role = ws_roles[w.name]

	if workspace and workspace not in ws_roles:
		workspace = None
	workspace = workspace or (workspaces[0].name if workspaces else None)

	data = frappe._dict(
		user=frappe.db.get_value("User", user, ["name", "full_name", "user_image", "email"], as_dict=True),
		is_admin=is_runway_admin(),
		workspaces=workspaces,
		workspace=workspace,
		projects=[],
		members=[],
		favorites=[],
		unread_count=0,
	)
	if not workspace:
		return data

	project_roles = get_project_roles()
	projects = frappe.get_all(
		"Runway Project",
		filters={"workspace": workspace, "name": ("in", list(project_roles) or [""])},
		fields=["*"],
		order_by="title asc",
	)
	data.projects = [project_payload(p, project_roles[p.name]) for p in projects]
	data.joinable_projects = frappe.get_all(
		"Runway Project",
		filters={
			"workspace": workspace,
			"network": "Public",
			"archived": 0,
			"name": ("not in", list(project_roles) or [""]),
		},
		fields=["name", "title", "identifier", "emoji", "color"],
	)
	data.members = get_workspace_members(workspace)
	data.favorites = frappe.get_all(
		"Runway Favorite",
		filters={"user": user},
		fields=["name", "reference_doctype", "reference_name"],
		order_by="creation asc",
	)
	data.unread_count = frappe.db.count(
		"Runway Notification", {"for_user": user, "read_at": ("is", "not set"), "archived_at": ("is", "not set")}
	)
	return data


def get_workspace_members(workspace: str):
	return frappe.db.sql(
		"""select m.name, m.user, m.role, u.full_name, u.user_image, u.email
		from `tabRunway Workspace Member` m join `tabUser` u on u.name = m.user
		where m.workspace = %s and u.enabled = 1 order by u.full_name""",
		workspace,
		as_dict=True,
	)


@frappe.whitelist()
def get_project(project: str):
	role = check_project_access(project)
	return project_payload(frappe.get_doc("Runway Project", project).as_dict(), role)


@frappe.whitelist()
def create_workspace(title: str, slug: str):
	if frappe.db.exists("Runway Workspace", slug):
		frappe.throw(_("Workspace URL {0} is taken").format(slug))
	doc = frappe.get_doc({"doctype": "Runway Workspace", "title": title, "slug": slug})
	doc.insert(ignore_permissions=True)
	ensure_runway_role(frappe.session.user)
	return doc.name


@frappe.whitelist()
def create_project(
	workspace: str,
	title: str,
	identifier: str,
	description: str | None = None,
	network: str = "Public",
	emoji: str | None = None,
	lead: str | None = None,
):
	role = check_workspace_access(workspace)
	if role == "Guest":
		frappe.throw(_("Guests cannot create projects"), frappe.PermissionError)
	doc = frappe.get_doc(
		{
			"doctype": "Runway Project",
			"workspace": workspace,
			"title": title,
			"identifier": identifier,
			"description": description,
			"network": network,
			"emoji": emoji,
			"lead": lead or frappe.session.user,
		}
	).insert(ignore_permissions=True)
	return get_project(doc.name)


@frappe.whitelist()
def update_project(project: str, values: dict | str):
	check_project_admin(project)
	values = frappe.parse_json(values)
	allowed = {
		"title",
		"description",
		"network",
		"emoji",
		"color",
		"lead",
		"default_assignee",
		"cycles_enabled",
		"modules_enabled",
		"views_enabled",
		"intake_enabled",
		"archived",
		"estimate",
	}
	doc = frappe.get_doc("Runway Project", project)
	doc.update({k: v for k, v in values.items() if k in allowed})
	doc.save(ignore_permissions=True)
	return get_project(project)


@frappe.whitelist()
def join_project(project: str):
	workspace, network = frappe.db.get_value("Runway Project", project, ["workspace", "network"])
	role = check_workspace_access(workspace)
	if network != "Public" or role == "Guest":
		frappe.throw(_("You need an invite to join this project"), frappe.PermissionError)
	_add_project_member(project, frappe.session.user, role if role != "Admin" else "Member")
	return get_project(project)


@frappe.whitelist()
def add_project_member(project: str, user: str, role: str = "Member"):
	check_project_admin(project)
	_add_project_member(project, user, role)


def _add_project_member(project, user, role):
	name = frappe.db.get_value("Runway Project Member", {"project": project, "user": user})
	if name:
		frappe.db.set_value("Runway Project Member", name, "role", role)
	else:
		frappe.get_doc(
			{"doctype": "Runway Project Member", "project": project, "user": user, "role": role}
		).insert(ignore_permissions=True)
	clear_access_cache()


@frappe.whitelist()
def remove_project_member(project: str, user: str):
	if user != frappe.session.user:
		check_project_admin(project)
	name = frappe.db.get_value("Runway Project Member", {"project": project, "user": user})
	if name:
		frappe.delete_doc("Runway Project Member", name, ignore_permissions=True)


@frappe.whitelist()
def get_project_members(project: str):
	check_project_access(project)
	return frappe.db.sql(
		"""select m.name, m.user, m.role, u.full_name, u.user_image, u.email
		from `tabRunway Project Member` m join `tabUser` u on u.name = m.user
		where m.project = %s order by u.full_name""",
		project,
		as_dict=True,
	)


@frappe.whitelist()
def invite_member(workspace: str, email: str, role: str = "Member"):
	"""Add a user to a workspace, creating their account when needed."""
	check_workspace_access(workspace, admin=True)
	if role not in ("Admin", "Member", "Guest"):
		frappe.throw(_("Invalid role"))
	email = email.strip().lower()
	if not frappe.db.exists("User", email):
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": email.split("@")[0],
				"send_welcome_email": 1,
				"user_type": "System User",
			}
		)
		user.insert(ignore_permissions=True)
	ensure_runway_role(email)
	name = frappe.db.get_value("Runway Workspace Member", {"workspace": workspace, "user": email})
	if name:
		frappe.db.set_value("Runway Workspace Member", name, "role", role)
	else:
		frappe.get_doc(
			{"doctype": "Runway Workspace Member", "workspace": workspace, "user": email, "role": role}
		).insert(ignore_permissions=True)
	clear_access_cache()
	return get_workspace_members(workspace)


@frappe.whitelist()
def update_workspace_member(workspace: str, user: str, role: str | None = None, remove: bool = False):
	check_workspace_access(workspace, admin=True)
	name = frappe.db.get_value("Runway Workspace Member", {"workspace": workspace, "user": user})
	if not name:
		frappe.throw(_("{0} is not a member").format(user))
	if frappe.parse_json(remove):
		frappe.delete_doc("Runway Workspace Member", name, ignore_permissions=True)
		frappe.db.delete(
			"Runway Project Member",
			{
				"user": user,
				"project": ("in", frappe.get_all("Runway Project", {"workspace": workspace}, pluck="name") or [""]),
			},
		)
	else:
		doc = frappe.get_doc("Runway Workspace Member", name)
		doc.role = role
		doc.save(ignore_permissions=True)
	clear_access_cache()
	return get_workspace_members(workspace)


def ensure_runway_role(user: str):
	if user in ("Administrator", "Guest"):
		return
	roles = frappe.get_roles(user)
	if "Runway User" not in roles:
		doc = frappe.get_doc("User", user)
		doc.add_roles("Runway User")


@frappe.whitelist()
def toggle_favorite(reference_doctype: str, reference_name: str):
	user = frappe.session.user
	name = frappe.db.get_value(
		"Runway Favorite",
		{"user": user, "reference_doctype": reference_doctype, "reference_name": reference_name},
	)
	if name:
		frappe.delete_doc("Runway Favorite", name, ignore_permissions=True)
		return False
	frappe.get_doc(reference_doctype, reference_name).check_permission("read")
	frappe.get_doc(
		{
			"doctype": "Runway Favorite",
			"user": user,
			"reference_doctype": reference_doctype,
			"reference_name": reference_name,
		}
	).insert(ignore_permissions=True)
	return True


@frappe.whitelist()
def record_visit(reference_doctype: str, reference_name: str):
	user = frappe.session.user
	name = frappe.db.get_value(
		"Runway Recent Visit",
		{"user": user, "reference_doctype": reference_doctype, "reference_name": reference_name},
	)
	if name:
		frappe.db.set_value("Runway Recent Visit", name, "visited_at", frappe.utils.now_datetime())
		return
	frappe.get_doc(
		{
			"doctype": "Runway Recent Visit",
			"user": user,
			"reference_doctype": reference_doctype,
			"reference_name": reference_name,
			"visited_at": frappe.utils.now_datetime(),
		}
	).insert(ignore_permissions=True)


@frappe.whitelist()
def set_estimate(project: str, estimate_type: str | None = None, points: list | str | None = None):
	"""Create or replace the project's estimate system. Empty points disable estimates."""
	check_project_admin(project)
	points = [str(p).strip() for p in (frappe.parse_json(points) or []) if str(p).strip()]
	current = frappe.db.get_value("Runway Project", project, "estimate")
	if not points:
		frappe.db.set_value("Runway Project", project, "estimate", None)
		return get_project(project)
	if current:
		est = frappe.get_doc("Runway Estimate", current)
	else:
		est = frappe.new_doc("Runway Estimate")
		est.project = project
		est.title = _("Estimate")
	est.estimate_type = estimate_type or "Points"
	est.set("points", [{"value": p} for p in points])
	est.save(ignore_permissions=True)
	frappe.db.set_value("Runway Project", project, "estimate", est.name)
	return get_project(project)
