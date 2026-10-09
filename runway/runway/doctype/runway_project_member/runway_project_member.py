# Copyright (c) 2026, Wildflower and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from runway.utils import clear_access_cache


class RunwayProjectMember(Document):
	def validate(self):
		if frappe.db.exists(
			"Runway Project Member",
			{"project": self.project, "user": self.user, "name": ("!=", self.name)},
		):
			frappe.throw(_("{0} is already a member of this project").format(self.user))
		workspace = frappe.db.get_value("Runway Project", self.project, "workspace")
		if not frappe.db.exists("Runway Workspace Member", {"workspace": workspace, "user": self.user}):
			frappe.throw(_("{0} must join the workspace before the project").format(self.user))

	def on_update(self):
		clear_access_cache()

	def after_delete(self):
		clear_access_cache()
