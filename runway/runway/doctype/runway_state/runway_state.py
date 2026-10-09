# Copyright (c) 2026, Wildflower and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class RunwayState(Document):
	def validate(self):
		if self.state_group == "Triage" and self.is_default:
			frappe.throw(_("The Triage state cannot be the default"))
		if self.is_new() and self.state_group == "Triage":
			if frappe.db.exists("Runway State", {"project": self.project, "state_group": "Triage"}):
				frappe.throw(_("A project has exactly one Triage state"))
		if not self.sequence:
			last = frappe.db.get_value(
				"Runway State", {"project": self.project}, "max(sequence)"
			)
			self.sequence = (last or 0) + 1000

	def on_update(self):
		if self.is_default:
			frappe.db.set_value(
				"Runway State",
				{"project": self.project, "name": ("!=", self.name), "is_default": 1},
				"is_default",
				0,
			)
		if self.has_value_changed("state_group") and not self.is_new():
			frappe.db.set_value(
				"Runway Work Item", {"state": self.name}, "state_group", self.state_group, update_modified=False
			)

	def on_trash(self):
		if self.is_default:
			frappe.throw(_("Make another state the default before deleting this one"))
		if self.state_group == "Triage":
			frappe.throw(_("The Triage state cannot be deleted"))
		if frappe.db.exists("Runway Work Item", {"state": self.name}):
			frappe.throw(_("Move work items out of {0} before deleting it").format(self.title))
