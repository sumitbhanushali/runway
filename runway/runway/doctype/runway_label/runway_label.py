# Copyright (c) 2026, Wildflower and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class RunwayLabel(Document):
	def validate(self):
		if self.parent_label:
			if self.parent_label == self.name:
				frappe.throw(_("A label cannot be its own parent"))
			if frappe.db.get_value("Runway Label", self.parent_label, "project") != self.project:
				frappe.throw(_("Parent label belongs to another project"))

	def on_trash(self):
		frappe.db.delete("Runway Work Item Label", {"label": self.name})
		frappe.db.set_value("Runway Label", {"parent_label": self.name}, "parent_label", None)
