# Copyright (c) 2026, Wildflower and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class RunwayEstimate(Document):
	def validate(self):
		values = [p.value.strip() for p in self.points]
		if len(values) != len(set(values)):
			frappe.throw(_("Estimate values must be unique"))
		if self.estimate_type == "Points":
			for v in values:
				try:
					float(v)
				except ValueError:
					frappe.throw(_("Point estimates must be numbers, got {0}").format(v))
