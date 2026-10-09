# Copyright (c) 2026, Wildflower and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from runway.utils import clear_access_cache


class RunwayWorkspaceMember(Document):
	def validate(self):
		if frappe.db.exists(
			"Runway Workspace Member",
			{"workspace": self.workspace, "user": self.user, "name": ("!=", self.name)},
		):
			frappe.throw(_("{0} is already a member of this workspace").format(self.user))
		if not self.is_new() and self.has_value_changed("role") and self.role != "Admin":
			self._ensure_another_admin()

	def on_trash(self):
		if self.role == "Admin":
			self._ensure_another_admin()

	def _ensure_another_admin(self):
		others = frappe.db.count(
			"Runway Workspace Member",
			{"workspace": self.workspace, "role": "Admin", "name": ("!=", self.name)},
		)
		if not others:
			frappe.throw(_("A workspace needs at least one admin"))

	def on_update(self):
		clear_access_cache()

	def after_delete(self):
		clear_access_cache()
