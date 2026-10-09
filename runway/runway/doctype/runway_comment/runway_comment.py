# Copyright (c) 2026, Wildflower and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import strip_html

from runway.utils import extract_mentions, get_project_role, get_subscribers, notify, now, subscribe


class RunwayComment(Document):
	def validate(self):
		if not strip_html(self.content or "").strip() and "<img" not in (self.content or ""):
			frappe.throw(_("Comment cannot be empty"))
		if not self.is_new() and self.has_value_changed("content"):
			self.edited_at = now()

	def after_insert(self):
		project, title = frappe.db.get_value("Runway Work Item", self.work_item, ["project", "title"])
		mentioned = {u for u in extract_mentions(self.content) if get_project_role(project, u)}
		snippet = strip_html(self.content or "")[:140]
		notify(mentioned, self.work_item, "mentioned", _("mentioned you on {0}: {1}").format(self.work_item, snippet))
		notify(
			set(get_subscribers(self.work_item)) - mentioned,
			self.work_item,
			"commented",
			_("commented on {0} {1}: {2}").format(self.work_item, title, snippet),
		)
		subscribe(self.work_item, self.owner)
		frappe.publish_realtime(
			"runway_item_updated", {"name": self.work_item, "project": project}, after_commit=True
		)

	def on_trash(self):
		frappe.db.delete("Runway Reaction", {"reference_doctype": self.doctype, "reference_name": self.name})
