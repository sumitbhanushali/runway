import csv
import io

import frappe
from frappe import _

from runway.api.work_items import query_items
from runway.utils import STATE_GROUPS, estimate_value

AXES = ("state", "state_group", "priority", "assignees", "labels", "cycle", "modules", "owner", "due_month")
PRIORITIES = ["Urgent", "High", "Medium", "Low", "None"]


def _keys(item, axis):
	if axis in ("assignees", "labels", "modules"):
		return item[axis] or [None]
	if axis == "due_month":
		return [str(item.due_date)[:7] if item.due_date else None]
	return [item.get(axis)]


def _labels(axis, keys):
	keys = [k for k in keys if k]
	if axis in ("assignees", "owner"):
		return dict(frappe.get_all("User", filters={"name": ("in", keys or [""])}, fields=["name", "full_name"], as_list=True))
	doctype = {"state": "Runway State", "labels": "Runway Label", "cycle": "Runway Cycle", "modules": "Runway Module"}.get(axis)
	if doctype:
		return dict(frappe.get_all(doctype, filters={"name": ("in", keys or [""])}, fields=["name", "title"], as_list=True))
	return {k: k for k in keys}


def _order(axis, keys, label_map):
	if axis == "state_group":
		return sorted(keys, key=lambda k: STATE_GROUPS.index(k) if k in STATE_GROUPS else 99)
	if axis == "priority":
		return sorted(keys, key=lambda k: PRIORITIES.index(k) if k in PRIORITIES else 99)
	return sorted(keys, key=lambda k: (k is None, str(label_map.get(k, k) or "")))


@frappe.whitelist()
def get_analytics(
	workspace: str | None = None,
	project: str | None = None,
	x_axis: str = "state_group",
	y_axis: str = "count",
	segment: str | None = None,
	filters: dict | str | None = None,
):
	if x_axis not in AXES or (segment and segment not in AXES):
		frappe.throw(_("Unsupported axis"))
	items = query_items(project=project, workspace=workspace, filters=filters, show_archived=1)

	points_by_project = {}

	def weight(i):
		if y_axis != "points":
			return 1
		if i.project not in points_by_project:
			est = frappe.db.get_value("Runway Project", i.project, "estimate")
			points_by_project[i.project] = (
				frappe.get_all("Runway Estimate Point", filters={"parent": est}, pluck="value", order_by="idx") if est else []
			)
		return estimate_value(i.estimate_point, points_by_project[i.project])

	data, seg_keys = {}, set()
	for i in items:
		w = weight(i)
		for x in _keys(i, x_axis):
			row = data.setdefault(x, {"value": 0, "segments": {}})
			row["value"] += w
			if segment:
				for s in _keys(i, segment):
					seg_keys.add(s)
					row["segments"][s] = row["segments"].get(s, 0) + w

	x_labels = _labels(x_axis, list(data))
	s_labels = _labels(segment, list(seg_keys)) if segment else {}
	rows = [
		{
			"key": k,
			"label": x_labels.get(k, k) or _("None"),
			"value": round(data[k]["value"], 2),
			"segments": {str(s): v for s, v in data[k]["segments"].items()},
		}
		for k in _order(x_axis, list(data), x_labels)
	]
	return {
		"x_axis": x_axis,
		"y_axis": y_axis,
		"segment": segment,
		"segments": [{"key": str(s), "label": s_labels.get(s, s) or _("None")} for s in _order(segment, list(seg_keys), s_labels)] if segment else [],
		"rows": rows,
		"total_items": len(items),
		"summary": {g: sum(1 for i in items if i.state_group == g) for g in STATE_GROUPS if g != "Triage"},
	}


@frappe.whitelist()
def export_csv(
	workspace: str | None = None,
	project: str | None = None,
	filters: dict | str | None = None,
):
	"""Work items as CSV text; the browser turns it into a download."""
	items = query_items(project=project, workspace=workspace, filters=filters, show_archived=1)
	states = dict(frappe.get_all("Runway State", fields=["name", "title"], filters={"name": ("in", list({i.state for i in items}) or [""])}, as_list=True))
	out = io.StringIO()
	w = csv.writer(out)
	w.writerow(["ID", "Title", "State", "Group", "Priority", "Assignees", "Labels", "Start", "Due", "Estimate", "Cycle", "Parent", "Created", "Completed"])
	for i in items:
		w.writerow(
			[
				i.name, i.title, states.get(i.state, i.state), i.state_group, i.priority, ", ".join(i.assignees),
				", ".join(i.labels), i.start_date or "", i.due_date or "", i.estimate_point or "", i.cycle or "",
				i.parent_item or "", i.creation, i.completed_at or "",
			]
		)
	return out.getvalue()
