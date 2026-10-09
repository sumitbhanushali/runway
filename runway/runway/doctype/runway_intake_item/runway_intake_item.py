# Copyright (c) 2026, Wildflower and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class RunwayIntakeItem(Document):
	def validate(self):
		if self.is_new() and not frappe.db.get_value("Runway Project", self.project, "intake_enabled"):
			frappe.throw(_("Intake is disabled for this project"))
		if frappe.db.get_value("Runway Work Item", self.work_item, "project") != self.project:
			frappe.throw(_("Work item belongs to another project"))
		if self.status == "Duplicate" and not self.duplicate_of:
			frappe.throw(_("Pick the work item this duplicates"))
		self.submitted_by = self.submitted_by or self.owner or frappe.session.user
