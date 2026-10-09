# Copyright (c) 2026, Wildflower and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class RunwayView(Document):
	def validate(self):
		if self.project:
			ws = frappe.db.get_value("Runway Project", self.project, "workspace")
			if self.workspace and ws != self.workspace:
				frappe.throw(_("Project belongs to another workspace"))
			self.workspace = ws
		for field in ("filters", "display_filters", "display_properties"):
			value = self.get(field)
			if isinstance(value, dict | list):
				self.set(field, frappe.as_json(value))
