import frappe
from frappe.utils import add_days, nowdate

from runway.api.work_items import query_items

TABS = {
	"assigned": lambda u: {"assignees": [u]},
	"created": lambda u: {"owner": [u]},
	"subscribed": lambda u: {"subscribed_by": u},
}


@frappe.whitelist()
def get_my_work(workspace: str, tab: str = "assigned", filters: dict | str | None = None, order_by: str = "-modified"):
	user = frappe.session.user
	f = frappe.parse_json(filters) if isinstance(filters, str) else (filters or {})
	f.update(TABS.get(tab, TABS["assigned"])(user))
	return query_items(workspace=workspace, filters=f, order_by=order_by)


@frappe.whitelist()
def get_home(workspace: str):
	user = frappe.session.user
	assigned = query_items(workspace=workspace, filters={"assignees": [user]})
	open_items = [i for i in assigned if i.state_group not in ("Completed", "Cancelled")]
	today = nowdate()
	week = add_days(today, 7)
	recents = frappe.get_all(
		"Runway Recent Visit",
		filters={"user": user},
		fields=["reference_doctype", "reference_name", "visited_at"],
		order_by="visited_at desc",
		limit=12,
	)
	titles = {}
	for r in recents:
		if r.reference_doctype == "Runway Work Item":
			titles.setdefault("Runway Work Item", []).append(r.reference_name)
	item_titles = dict(
		frappe.get_all(
			"Runway Work Item",
			filters={"name": ("in", titles.get("Runway Work Item") or [""])},
			fields=["name", "title"],
			as_list=True,
		)
	)
	for r in recents:
		if r.reference_doctype == "Runway Work Item":
			r.title = item_titles.get(r.reference_name)
		elif frappe.db.exists(r.reference_doctype, r.reference_name):
			r.title = frappe.db.get_value(r.reference_doctype, r.reference_name, "title")
	return {
		"counts": {
			"open": len(open_items),
			"overdue": sum(1 for i in open_items if i.due_date and str(i.due_date) < today),
			"due_this_week": sum(1 for i in open_items if i.due_date and today <= str(i.due_date) <= week),
			"completed": sum(1 for i in assigned if i.state_group == "Completed"),
		},
		"upcoming": sorted(
			[i for i in open_items if i.due_date], key=lambda i: str(i.due_date)
		)[:8],
		"recents": [r for r in recents if r.get("title")],
	}
