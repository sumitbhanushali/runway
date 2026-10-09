# Copyright (c) 2026, Wildflower and contributors
# For license information, please see license.txt

import time

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate

from runway.utils import get_subscribers, log_activity, notify, now, subscribe

# Fields recorded in the activity log, with how to read them for comparison.
TRACKED_FIELDS = (
	"title",
	"description",
	"state",
	"priority",
	"start_date",
	"due_date",
	"parent_item",
	"estimate_point",
	"cycle",
	"archived_at",
	"is_draft",
)
TABLE_FIELDS = {"assignees": "user", "labels": "label", "modules": "module"}


class RunwayWorkItem(Document):
	def autoname(self):
		# Lock the project row so concurrent inserts never share a sequence number.
		row = frappe.db.sql(
			"select item_sequence from `tabRunway Project` where name=%s for update", self.project
		)
		if not row:
			frappe.throw(_("Project {0} not found").format(self.project))
		seq = (row[0][0] or 0) + 1
		frappe.db.set_value("Runway Project", self.project, "item_sequence", seq, update_modified=False)
		self.sequence_id = seq
		self.name = f"{self.project}-{seq}"

	def before_validate(self):
		self.title = (self.title or "").strip()
		if not self.state:
			self.state = frappe.db.get_value(
				"Runway State", {"project": self.project, "is_default": 1}, "name"
			) or frappe.db.get_value("Runway State", {"project": self.project, "state_group": "Backlog"}, "name")
		if not self.sort_order:
			self.sort_order = time.time()
		self.priority = self.priority or "None"

	def validate(self):
		if not self.title:
			frappe.throw(_("Title is required"))
		if not self.is_new() and self.has_value_changed("project"):
			frappe.throw(_("Work items cannot move between projects"))

		state = frappe.db.get_value("Runway State", self.state, ["project", "state_group"], as_dict=True)
		if not state or state.project != self.project:
			frappe.throw(_("State {0} does not belong to project {1}").format(self.state, self.project))
		self.state_group = state.state_group
		if self.state_group == "Completed":
			self.completed_at = self.completed_at or now()
		else:
			self.completed_at = None

		if self.start_date and self.due_date and getdate(self.due_date) < getdate(self.start_date):
			frappe.throw(_("Due date cannot be before start date"))

		self.validate_parent()
		self.validate_project_links()
		self.dedupe_tables()

	def validate_parent(self):
		if not self.parent_item:
			return
		if self.parent_item == self.name:
			frappe.throw(_("A work item cannot be its own parent"))
		seen = {self.name}
		current = self.parent_item
		while current:
			if current in seen:
				frappe.throw(_("This parent would create a cycle of sub-work-items"))
			seen.add(current)
			parent = frappe.db.get_value("Runway Work Item", current, ["project", "parent_item"], as_dict=True)
			if not parent:
				frappe.throw(_("Parent work item {0} not found").format(current))
			if current == self.parent_item and parent.project != self.project:
				frappe.throw(_("Parent must be in the same project"))
			current = parent.parent_item

	def validate_project_links(self):
		def check(doctype, names):
			names = [n for n in names if n]
			if not names:
				return
			found = frappe.get_all(
				doctype, filters={"name": ("in", names), "project": self.project}, pluck="name"
			)
			missing = set(names) - set(found)
			if missing:
				frappe.throw(_("{0} {1} belongs to another project").format(doctype, ", ".join(missing)))

		check("Runway Label", [r.label for r in self.labels])
		check("Runway Module", [r.module for r in self.modules])
		if self.cycle:
			check("Runway Cycle", [self.cycle])
			if self.has_value_changed("cycle") and frappe.db.get_value("Runway Cycle", self.cycle, "completed_at"):
				frappe.throw(_("Cannot add work items to a completed cycle"))

	def dedupe_tables(self):
		for table, field in TABLE_FIELDS.items():
			seen, rows = set(), []
			for row in self.get(table):
				key = row.get(field)
				if key and key not in seen:
					seen.add(key)
					rows.append(row)
			self.set(table, rows)

	def on_update(self):
		before = self.get_doc_before_save()
		actor = frappe.session.user
		subscribe(self.name, self.owner)
		for user in self._table_values("assignees"):
			subscribe(self.name, user)

		if not before:
			log_activity(self.name, "created")
			notify(
				set(self._table_values("assignees")),
				self.name,
				"assigned",
				_("assigned you to {0} {1}").format(self.name, self.title),
			)
			self._broadcast()
			return

		changes = []
		for field in TRACKED_FIELDS:
			old, new = before.get(field), self.get(field)
			if (old or None) != (new or None) and str(old or "") != str(new or ""):
				if field == "description":
					old, new = None, None  # Version history keeps the full text.
				changes.append((field, old, new))
		for table in TABLE_FIELDS:
			old = set(self._table_values(table, before))
			new = set(self._table_values(table))
			if old != new:
				changes.append((table, ", ".join(sorted(old)), ", ".join(sorted(new))))

		for field, old, new in changes:
			log_activity(self.name, "updated", field, old, new, actor)

		if not changes:
			return
		changed = {c[0] for c in changes}
		added = set(self._table_values("assignees")) - set(self._table_values("assignees", before))
		notify(added, self.name, "assigned", _("assigned you to {0} {1}").format(self.name, self.title))
		others = set(get_subscribers(self.name)) - added
		if "state" in changed:
			state_title = frappe.db.get_value("Runway State", self.state, "title")
			notify(others, self.name, "state_changed", _("moved {0} to {1}").format(self.name, state_title))
		elif changed - {"sort_order"}:
			fields = ", ".join(sorted(changed))
			notify(others, self.name, "updated", _("updated {0} on {1}").format(fields, self.name))
		self._broadcast()

	def _table_values(self, table, doc=None):
		doc = doc or self
		field = TABLE_FIELDS[table]
		return [r.get(field) for r in (doc.get(table) or []) if r.get(field)]

	def _broadcast(self):
		frappe.publish_realtime(
			"runway_item_updated",
			{"name": self.name, "project": self.project},
			doctype="Runway Project",
			docname=self.project,
			after_commit=True,
		)

	def on_trash(self):
		frappe.db.set_value("Runway Work Item", {"parent_item": self.name}, "parent_item", None)
		for doctype, field in (
			("Runway Work Item Relation", "work_item"),
			("Runway Work Item Relation", "related_item"),
			("Runway Work Item Link", "work_item"),
			("Runway Activity", "work_item"),
			("Runway Subscription", "work_item"),
			("Runway Notification", "work_item"),
			("Runway Intake Item", "work_item"),
		):
			frappe.db.delete(doctype, {field: self.name})
		for name in frappe.get_all("Runway Comment", filters={"work_item": self.name}, pluck="name"):
			frappe.delete_doc("Runway Comment", name, ignore_permissions=True, force=True)
		frappe.db.delete("Runway Favorite", {"reference_doctype": self.doctype, "reference_name": self.name})
		frappe.db.delete(
			"Runway Recent Visit", {"reference_doctype": self.doctype, "reference_name": self.name}
		)

