# Copyright (c) 2026, Wildflower and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, nowdate


def compute_status(start_date, end_date, completed_at) -> str:
	if completed_at:
		return "Completed"
	if not start_date or not end_date:
		return "Draft"
	today = getdate(nowdate())
	if today < getdate(start_date):
		return "Upcoming"
	if today <= getdate(end_date):
		return "Current"
	return "Completed"


class RunwayCycle(Document):
	def validate(self):
		if not frappe.db.get_value("Runway Project", self.project, "cycles_enabled"):
			frappe.throw(_("Cycles are disabled for this project"))
		if bool(self.start_date) != bool(self.end_date):
			frappe.throw(_("Set both start and end dates, or neither"))
		if self.start_date and self.end_date:
			if getdate(self.end_date) < getdate(self.start_date):
				frappe.throw(_("End date cannot be before start date"))
			self.validate_overlap()
		if not self.is_new() and self.completed_at and self.has_value_changed("end_date"):
			frappe.throw(_("A completed cycle cannot be rescheduled"))
		self.status = compute_status(self.start_date, self.end_date, self.completed_at)

	def validate_overlap(self):
		clash = frappe.db.get_value(
			"Runway Cycle",
			{
				"project": self.project,
				"name": ("!=", self.name or ""),
				"start_date": ("<=", self.end_date),
				"end_date": (">=", self.start_date),
			},
			"title",
		)
		if clash:
			frappe.throw(_("Dates overlap with cycle {0}").format(frappe.bold(clash)), title=_("Overlapping cycle"))

	def on_trash(self):
		frappe.db.set_value("Runway Work Item", {"cycle": self.name}, "cycle", None)


def update_cycle_statuses():
	"""Daily: keep the stored status in step with the calendar."""
	for c in frappe.get_all(
		"Runway Cycle",
		filters={"status": ("in", ["Draft", "Upcoming", "Current"])},
		fields=["name", "start_date", "end_date", "completed_at", "status"],
	):
		status = compute_status(c.start_date, c.end_date, c.completed_at)
		if status != c.status:
			frappe.db.set_value("Runway Cycle", c.name, "status", status, update_modified=False)
