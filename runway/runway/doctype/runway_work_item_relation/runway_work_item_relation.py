# Copyright (c) 2026, Wildflower and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from runway.utils import log_activity


class RunwayWorkItemRelation(Document):
	def validate(self):
		if self.work_item == self.related_item:
			frappe.throw(_("A work item cannot relate to itself"))
		pair = [self.work_item, self.related_item]
		if frappe.db.exists(
			"Runway Work Item Relation",
			{"work_item": ("in", pair), "related_item": ("in", pair), "name": ("!=", self.name or "")},
		):
			frappe.throw(_("These work items are already related"))
		ws = frappe.get_all(
			"Runway Work Item", filters={"name": ("in", pair)}, fields=["project"], pluck="project"
		)
		workspaces = {frappe.db.get_value("Runway Project", p, "workspace") for p in ws}
		if len(workspaces) > 1:
			frappe.throw(_("Related work items must be in the same workspace"))

	def after_insert(self):
		log_activity(self.work_item, "added_relation", self.relation_type, None, self.related_item)

	def on_trash(self):
		log_activity(self.work_item, "removed_relation", self.relation_type, self.related_item, None)
