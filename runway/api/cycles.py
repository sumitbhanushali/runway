from datetime import timedelta

import frappe
from frappe import _
from frappe.utils import get_datetime, getdate, nowdate

from runway.api.work_items import query_items
from runway.runway.doctype.runway_cycle.runway_cycle import compute_status
from runway.utils import DONE_GROUPS, STATE_GROUPS, check_project_access, estimate_value, now


def _points(project):
	estimate = frappe.db.get_value("Runway Project", project, "estimate")
	if not estimate:
		return []
	return frappe.get_all(
		"Runway Estimate Point", filters={"parent": estimate, "parenttype": "Runway Estimate"}, pluck="value", order_by="idx"
	)


def progress(items, points=None) -> dict:
	by_group = {g: 0 for g in STATE_GROUPS}
	pts_by_group = {g: 0.0 for g in STATE_GROUPS}
	for i in items:
		by_group[i.state_group] = by_group.get(i.state_group, 0) + 1
		pts_by_group[i.state_group] = pts_by_group.get(i.state_group, 0) + estimate_value(i.estimate_point, points)
	total = sum(v for g, v in by_group.items() if g != "Cancelled")
	done = by_group["Completed"]
	total_pts = sum(v for g, v in pts_by_group.items() if g != "Cancelled")
	return {
		"total": total,
		"completed": done,
		"percent": round(done * 100 / total) if total else 0,
		"by_group": by_group,
		"points_total": total_pts,
		"points_completed": pts_by_group["Completed"],
	}


@frappe.whitelist()
def get_cycles(project: str):
	check_project_access(project)
	points = _points(project)
	cycles = frappe.get_all(
		"Runway Cycle",
		filters={"project": project},
		fields=["*"],
		order_by="start_date desc, creation desc",
	)
	items = query_items(project=project, filters={"cycle": [c.name for c in cycles] or [""]})
	for c in cycles:
		c.status = compute_status(c.start_date, c.end_date, c.completed_at)
		if c.completed_at and c.progress_snapshot:
			c.progress = frappe.parse_json(c.progress_snapshot)
		else:
			c.progress = progress([i for i in items if i.cycle == c.name], points)
	return cycles


@frappe.whitelist()
def get_burndown(cycle: str, by: str = "count"):
	c = frappe.get_doc("Runway Cycle", cycle)
	c.check_permission("read")
	if not c.start_date or not c.end_date:
		return {"days": [], "ideal": [], "actual": []}
	points = _points(c.project)
	if c.completed_at and c.progress_snapshot:
		snap = frappe.parse_json(c.progress_snapshot)
		if snap.get("burndown") and snap["burndown"].get(by):
			return snap["burndown"][by]
	items = [i for i in query_items(project=c.project, filters={"cycle": [cycle]}, show_archived=1) if i.state_group != "Cancelled"]
	return _burndown(items, c.start_date, c.end_date, by, points)


def _burndown(items, start, end, by, points):
	weight = (lambda i: estimate_value(i.estimate_point, points)) if by == "points" else (lambda i: 1)
	total = sum(weight(i) for i in items)
	start, end = getdate(start), getdate(end)
	days = (end - start).days + 1
	today = getdate(nowdate())
	out = {"days": [], "ideal": [], "actual": [], "total": total}
	for n in range(days):
		day = start + timedelta(days=n)
		out["days"].append(str(day))
		out["ideal"].append(round(total - total * n / max(days - 1, 1), 2))
		if day > today:
			out["actual"].append(None)
			continue
		done = sum(weight(i) for i in items if i.completed_at and getdate(get_datetime(i.completed_at)) <= day)
		out["actual"].append(round(total - done, 2))
	return out


@frappe.whitelist()
def complete_cycle(cycle: str, transfer_to: str | None = None):
	"""Freeze progress and optionally move unfinished items to another cycle."""
	c = frappe.get_doc("Runway Cycle", cycle)
	c.check_permission("write")
	if c.completed_at:
		frappe.throw(_("Cycle is already completed"))
	points = _points(c.project)
	items = query_items(project=c.project, filters={"cycle": [cycle]}, show_archived=1)
	pending = [i for i in items if i.state_group not in DONE_GROUPS]

	if transfer_to:
		target = frappe.get_doc("Runway Cycle", transfer_to)
		if target.project != c.project or target.completed_at or target.name == cycle:
			frappe.throw(_("Pick an open cycle in the same project"))

	scoped = [i for i in items if i.state_group != "Cancelled"]
	snapshot = progress(items, points)
	snapshot["items"] = [i.name for i in items]
	snapshot["transferred"] = [i.name for i in pending] if transfer_to else []
	snapshot["transferred_to"] = transfer_to
	if c.start_date and c.end_date:
		snapshot["burndown"] = {
			by: _burndown(scoped, c.start_date, c.end_date, by, points) for by in ("count", "points")
		}

	if transfer_to:
		for i in pending:
			doc = frappe.get_doc("Runway Work Item", i.name)
			doc.cycle = transfer_to
			doc.save()

	c.completed_at = now()
	c.progress_snapshot = frappe.as_json(snapshot)
	c.save()
	return {"transferred": len(snapshot["transferred"]), "pending": len(pending)}


@frappe.whitelist()
def transfer_items(cycle: str, transfer_to: str):
	"""Move unfinished items without completing (used for already-ended cycles)."""
	c = frappe.get_doc("Runway Cycle", cycle)
	c.check_permission("write")
	moved = 0
	for i in query_items(project=c.project, filters={"cycle": [cycle]}):
		if i.state_group not in DONE_GROUPS:
			doc = frappe.get_doc("Runway Work Item", i.name)
			doc.cycle = transfer_to
			doc.save()
			moved += 1
	return moved
