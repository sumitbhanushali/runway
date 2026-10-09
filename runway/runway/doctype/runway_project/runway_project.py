# Copyright (c) 2026, Wildflower and contributors
# For license information, please see license.txt

import re

import frappe
from frappe import _
from frappe.model.document import Document

from runway.utils import DEFAULT_LABELS, DEFAULT_STATES, clear_access_cache


class RunwayProject(Document):
	def validate(self):
		self.identifier = (self.identifier or "").strip().upper()
		if not re.fullmatch(r"[A-Z][A-Z0-9]{0,11}", self.identifier):
			frappe.throw(_("Identifier must start with a letter and use up to 12 letters or digits"))
		if self.estimate and frappe.db.get_value("Runway Estimate", self.estimate, "project") != self.name:
			frappe.throw(_("Estimate belongs to another project"))

	def after_insert(self):
		self.seed_defaults()
		frappe.get_doc(
			{
				"doctype": "Runway Project Member",
				"project": self.name,
				"user": frappe.session.user,
				"role": "Admin",
			}
		).insert(ignore_permissions=True)
		clear_access_cache()

	def on_update(self):
		clear_access_cache()

	def seed_defaults(self):
		for idx, (title, group, color, is_default) in enumerate(DEFAULT_STATES):
			frappe.get_doc(
				{
					"doctype": "Runway State",
					"project": self.name,
					"title": title,
					"state_group": group,
					"color": color,
					"is_default": is_default,
					"sequence": (idx + 1) * 1000,
				}
			).insert(ignore_permissions=True)
		for title, color in DEFAULT_LABELS:
			frappe.get_doc(
				{"doctype": "Runway Label", "project": self.name, "title": title, "color": color}
			).insert(ignore_permissions=True)

	def on_trash(self):
		if frappe.db.exists("Runway Work Item", {"project": self.name}):
			frappe.throw(_("Archive the project instead, or delete its work items first"))
		self.db_set("estimate", None)
		# States are removed wholesale: their own guards (default / Triage) only
		# make sense while the project lives on.
		frappe.db.delete("Runway State", {"project": self.name})
		for doctype in (
			"Runway Project Member",
			"Runway Label",
			"Runway Cycle",
			"Runway Module",
			"Runway Estimate",
			"Runway View",
			"Runway Intake Item",
		):
			for name in frappe.get_all(doctype, filters={"project": self.name}, pluck="name"):
				frappe.delete_doc(doctype, name, ignore_permissions=True, force=True)
		clear_access_cache()
