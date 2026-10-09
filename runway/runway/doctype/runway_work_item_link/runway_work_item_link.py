# Copyright (c) 2026, Wildflower and contributors
# For license information, please see license.txt

from frappe.model.document import Document

from runway.utils import log_activity


class RunwayWorkItemLink(Document):
	def validate(self):
		self.url = (self.url or "").strip()
		if self.url and "://" not in self.url:
			self.url = "https://" + self.url
		self.title = self.title or self.url

	def after_insert(self):
		log_activity(self.work_item, "added_link", "link", None, self.url)
