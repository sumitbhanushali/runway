import frappe
from frappe.utils import cint, now_datetime

FILTERS = {
	"all": {"archived_at": ("is", "not set")},
	"unread": {"archived_at": ("is", "not set"), "read_at": ("is", "not set")},
	"archived": {"archived_at": ("is", "set")},
	"snoozed": {"archived_at": ("is", "not set")},
}


@frappe.whitelist()
def get_inbox(tab: str = "all", limit: int = 100):
	user = frappe.session.user
	filters = {"for_user": user, **FILTERS.get(tab, FILTERS["all"])}
	rows = frappe.get_all(
		"Runway Notification",
		filters=filters,
		fields=["name", "work_item", "actor", "notification_type", "message", "read_at", "snoozed_until", "archived_at", "creation"],
		order_by="creation desc",
		limit=cint(limit) or 100,
	)
	now = now_datetime()
	if tab != "archived":
		is_snoozed = lambda r: bool(r.snoozed_until and r.snoozed_until > now)  # noqa: E731
		rows = [r for r in rows if is_snoozed(r) == (tab == "snoozed")]
	items = {
		w.name: w
		for w in frappe.get_all(
			"Runway Work Item",
			filters={"name": ("in", [r.work_item for r in rows if r.work_item] or [""])},
			fields=["name", "title", "project", "state_group"],
		)
	}
	for r in rows:
		r.item = items.get(r.work_item)
	return rows


def _mine(names):
	names = frappe.parse_json(names) if isinstance(names, str) and names.startswith("[") else names
	names = names if isinstance(names, list) else [names]
	return frappe.get_all(
		"Runway Notification", filters={"name": ("in", names or [""]), "for_user": frappe.session.user}, pluck="name"
	)


def _set(names, field, value):
	for n in _mine(names):
		frappe.db.set_value("Runway Notification", n, field, value, update_modified=False)


@frappe.whitelist()
def mark_read(names, unread: int = 0):
	_set(names, "read_at", None if cint(unread) else now_datetime())


@frappe.whitelist()
def mark_all_read():
	frappe.db.set_value(
		"Runway Notification",
		{"for_user": frappe.session.user, "read_at": ("is", "not set")},
		"read_at",
		now_datetime(),
		update_modified=False,
	)


@frappe.whitelist()
def archive(names, unarchive: int = 0):
	_set(names, "archived_at", None if cint(unarchive) else now_datetime())


@frappe.whitelist()
def snooze(names, until: str | None = None):
	_set(names, "snoozed_until", until)


@frappe.whitelist()
def unread_count():
	return frappe.db.count(
		"Runway Notification",
		{"for_user": frappe.session.user, "read_at": ("is", "not set"), "archived_at": ("is", "not set")},
	)
