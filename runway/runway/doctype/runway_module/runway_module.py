# Copyright (c) 2026, Wildflower and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate


class RunwayModule(Document):
	def validate(self):
		if not frappe.db.get_value("Runway Project", self.project, "modules_enabled"):
			frappe.throw(_("Modules are disabled for this project"))
		if self.start_date and self.target_date and getdate(self.target_date) < getdate(self.start_date):
			frappe.throw(_("Target date cannot be before start date"))

	def on_trash(self):
		frappe.db.delete("Runway Work Item Module", {"module": self.name})
