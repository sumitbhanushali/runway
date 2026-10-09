import frappe
from frappe import _

from runway.utils import check_project_access, notify


def _triage_state(project):
	state = frappe.db.get_value("Runway State", {"project": project, "state_group": "Triage"})
	if not state:
		state = frappe.get_doc(
			{"doctype": "Runway State", "project": project, "title": "Triage", "state_group": "Triage", "color": "#4e5355"}
		).insert(ignore_permissions=True).name
	return state


@frappe.whitelist()
def submit(project: str, title: str, description: str | None = None, priority: str = "None", source: str = "In-app"):
	check_project_access(project)
	if not frappe.db.get_value("Runway Project", project, "intake_enabled"):
		frappe.throw(_("Intake is disabled for this project"))
	item = frappe.get_doc(
		{
			"doctype": "Runway Work Item",
			"project": project,
			"title": title,
			"description": description,
			"priority": priority,
			"state": _triage_state(project),
		}
	).insert(ignore_permissions=True)
	intake = frappe.get_doc(
		{
			"doctype": "Runway Intake Item",
			"project": project,
			"work_item": item.name,
			"source": source,
			"submitted_by": frappe.session.user,
		}
	).insert(ignore_permissions=True)
	admins = frappe.get_all("Runway Project Member", filters={"project": project, "role": "Admin"}, pluck="user")
	notify(admins, item.name, "intake", _("submitted {0} to intake: {1}").format(item.name, title))
	return intake.name


@frappe.whitelist()
def get_intake(project: str, status: str | None = "Pending"):
	check_project_access(project)
	filters = {"project": project}
	if status == "Pending":
		filters["status"] = ("in", ["Pending", "Snoozed"])
	elif status:
		filters["status"] = ("in", ["Accepted", "Declined", "Duplicate"]) if status == "Closed" else status
	rows = frappe.get_all(
		"Runway Intake Item",
		filters=filters,
		fields=["name", "work_item", "status", "snoozed_till", "duplicate_of", "source", "submitted_by", "creation"],
		order_by="creation desc",
	)
	today = frappe.utils.getdate()
	titles = {
		w.name: w
		for w in frappe.get_all(
			"Runway Work Item",
			filters={"name": ("in", [r.work_item for r in rows] or [""])},
			fields=["name", "title", "priority", "state_group"],
		)
	}
	out = []
	for r in rows:
		r.snoozed = r.status == "Snoozed" and r.snoozed_till and frappe.utils.getdate(r.snoozed_till) > today
		r.item = titles.get(r.work_item)
		out.append(r)
	return out


def _review(intake_name):
	doc = frappe.get_doc("Runway Intake Item", intake_name)
	role = check_project_access(doc.project, write=True)
	if role not in ("Admin", "Member"):
		frappe.throw(_("Only project members can triage intake"), frappe.PermissionError)
	return doc


def _close(doc, status, message, state=None, **extra):
	item = frappe.get_doc("Runway Work Item", doc.work_item)
	if state:
		item.state = state
		item.save(ignore_permissions=True)
	doc.status = status
	doc.update(extra)
	doc.save(ignore_permissions=True)
	notify([doc.submitted_by], item.name, "intake", message.format(item.name, item.title))
	return doc.status


@frappe.whitelist()
def accept(intake: str, state: str | None = None):
	doc = _review(intake)
	state = state or frappe.db.get_value("Runway State", {"project": doc.project, "is_default": 1})
	return _close(doc, "Accepted", _("accepted your request {0} {1}"), state=state)


@frappe.whitelist()
def decline(intake: str):
	doc = _review(intake)
	cancelled = frappe.db.get_value("Runway State", {"project": doc.project, "state_group": "Cancelled"})
	return _close(doc, "Declined", _("declined your request {0} {1}"), state=cancelled)


@frappe.whitelist()
def mark_duplicate(intake: str, duplicate_of: str):
	doc = _review(intake)
	if duplicate_of == doc.work_item:
		frappe.throw(_("A request cannot duplicate itself"))
	cancelled = frappe.db.get_value("Runway State", {"project": doc.project, "state_group": "Cancelled"})
	frappe.get_doc(
		{"doctype": "Runway Work Item Relation", "work_item": doc.work_item, "related_item": duplicate_of, "relation_type": "duplicate"}
	).insert(ignore_permissions=True)
	return _close(
		doc, "Duplicate", _("marked your request {0} {1} as a duplicate"), state=cancelled, duplicate_of=duplicate_of
	)


@frappe.whitelist()
def snooze(intake: str, until: str | None = None):
	doc = _review(intake)
	doc.status = "Snoozed" if until else "Pending"
	doc.snoozed_till = until
	doc.save(ignore_permissions=True)
	return doc.status
