# Copyright (c) 2026, Wildflower and contributors
# For license information, please see license.txt

import re

import frappe
from frappe import _
from frappe.model.document import Document

from runway.utils import clear_access_cache


class RunwayWorkspace(Document):
	def validate(self):
		self.slug = (self.slug or frappe.scrub(self.title)).strip().lower().replace("_", "-")
		if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,47}", self.slug):
			frappe.throw(_("Workspace URL may only contain lowercase letters, numbers and dashes"))

	def after_insert(self):
		frappe.get_doc(
			{
				"doctype": "Runway Workspace Member",
				"workspace": self.name,
				"user": frappe.session.user,
				"role": "Admin",
			}
		).insert(ignore_permissions=True)
		clear_access_cache()

	def on_trash(self):
		if frappe.db.exists("Runway Project", {"workspace": self.name}):
			frappe.throw(_("Delete the workspace's projects first"))
		frappe.db.delete("Runway Workspace Member", {"workspace": self.name})
