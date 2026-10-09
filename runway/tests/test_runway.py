import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, nowdate

from runway.api import boot, cycles, intake, work_items
from runway.api.analytics import get_analytics
from runway.utils import clear_access_cache


OWNER = "rw-owner@runway.test"
MEMBER = "rw-member@runway.test"
OUTSIDER = "rw-outsider@runway.test"


def make_user(email):
	if not frappe.db.exists("User", email):
		frappe.get_doc(
			{"doctype": "User", "email": email, "first_name": email.split("@")[0], "send_welcome_email": 0}
		).insert(ignore_permissions=True)
	frappe.get_doc("User", email).add_roles("Runway User")


class TestRunway(IntegrationTestCase):
	def setUp(self):
		for u in (OWNER, MEMBER, OUTSIDER):
			make_user(u)
		clear_access_cache()
		frappe.set_user(OWNER)
		self.ws = boot.create_workspace("Runway Test", f"rw-{frappe.generate_hash(length=6).lower()}")
		boot.invite_member(self.ws, MEMBER, "Member")
		ident = "T" + frappe.generate_hash(length=5).upper().replace("0", "A")
		self.project = boot.create_project(self.ws, "Test Project", ident)["name"]

	def tearDown(self):
		frappe.set_user("Administrator")
		clear_access_cache()
		frappe.db.rollback()

	def new_item(self, title="Item", **values):
		return work_items.create_item(self.project, {"title": title, **values})

	def state(self, group):
		return frappe.db.get_value("Runway State", {"project": self.project, "state_group": group})

	# ------------------------------------------------------------------ projects

	def test_project_seeds_default_states_and_owner(self):
		states = frappe.get_all("Runway State", filters={"project": self.project}, pluck="title", order_by="sequence")
		self.assertEqual(states, ["Backlog", "Todo", "In Progress", "Done", "Cancelled", "Triage"])
		self.assertEqual(frappe.db.get_value("Runway State", {"project": self.project, "is_default": 1}, "title"), "Backlog")
		self.assertEqual(
			frappe.db.get_value("Runway Project Member", {"project": self.project, "user": OWNER}, "role"), "Admin"
		)

	def test_delete_empty_project(self):
		frappe.delete_doc("Runway Project", self.project)
		self.assertFalse(frappe.db.exists("Runway State", {"project": self.project}))
		self.assertFalse(frappe.db.exists("Runway Project Member", {"project": self.project}))

	def test_delete_project_with_items_is_blocked(self):
		self.new_item("Keep me")
		with self.assertRaises(frappe.ValidationError):
			frappe.delete_doc("Runway Project", self.project)

	def test_identifier_is_validated(self):
		with self.assertRaises(frappe.ValidationError):
			boot.create_project(self.ws, "Bad", "1ABC")

	# ---------------------------------------------------------------- work items

	def test_sequence_numbering(self):
		a, b = self.new_item("A"), self.new_item("B")
		self.assertEqual(a.name, f"{self.project}-1")
		self.assertEqual(b.name, f"{self.project}-2")
		self.assertEqual(frappe.db.get_value("Runway Project", self.project, "item_sequence"), 2)
		self.assertEqual(a.state_group, "Backlog")

	def test_parent_cycle_is_rejected(self):
		a = self.new_item("A")
		b = self.new_item("B", parent_item=a.name)
		with self.assertRaises(frappe.ValidationError):
			work_items.update_item(a.name, {"parent_item": b.name})

	def test_sub_item_progress_rollup(self):
		parent = self.new_item("Parent")
		self.new_item("Child 1", parent_item=parent.name)
		child = self.new_item("Child 2", parent_item=parent.name)
		work_items.update_item(child.name, {"state": self.state("Completed")})
		row = work_items.get_row(parent.name)
		self.assertEqual((row.sub_items_count, row.sub_items_done), (2, 1))

	def test_activity_and_completion(self):
		item = self.new_item("Track me")
		work_items.update_item(item.name, {"priority": "High", "state": self.state("Completed"), "assignees": [MEMBER]})
		acts = frappe.get_all("Runway Activity", filters={"work_item": item.name}, fields=["verb", "field", "new_value"])
		fields = {a.field for a in acts if a.verb == "updated"}
		self.assertTrue({"priority", "state", "assignees"} <= fields)
		self.assertTrue(any(a.verb == "created" for a in acts))
		self.assertTrue(frappe.db.get_value("Runway Work Item", item.name, "completed_at"))
		self.assertTrue(
			frappe.db.exists("Runway Notification", {"for_user": MEMBER, "work_item": item.name, "notification_type": "assigned"})
		)

	def test_mention_notifies(self):
		item = self.new_item("Mention")
		html = f'<p>hey <span class="mention" data-type="mention" data-id="{MEMBER}" data-label="m">@m</span></p>'
		work_items.add_comment(item.name, html)
		self.assertTrue(
			frappe.db.exists("Runway Notification", {"for_user": MEMBER, "notification_type": "mentioned"})
		)

	def test_relations_inverse(self):
		a, b = self.new_item("A"), self.new_item("B")
		work_items.add_relation(a.name, b.name, "blocking")
		rel_a = work_items.get_relations(a.name)
		rel_b = work_items.get_relations(b.name)
		self.assertEqual(rel_a[0]["relation_type"], "blocking")
		self.assertEqual(rel_b[0]["relation_type"], "blocked_by")

	def test_filters(self):
		self.new_item("Urgent one", priority="Urgent", assignees=[MEMBER])
		self.new_item("Low one", priority="Low")
		rows = work_items.get_items(project=self.project, filters={"priority": ["Urgent"]})
		self.assertEqual([r.title for r in rows], ["Urgent one"])
		rows = work_items.get_items(project=self.project, filters={"assignees": [MEMBER]})
		self.assertEqual(len(rows), 1)

	# -------------------------------------------------------------------- cycles

	def _cycle(self, title, start, end):
		return frappe.get_doc(
			{"doctype": "Runway Cycle", "project": self.project, "title": title, "start_date": start, "end_date": end}
		).insert()

	def test_cycle_overlap_rejected(self):
		self._cycle("C1", nowdate(), add_days(nowdate(), 13))
		with self.assertRaises(frappe.ValidationError):
			self._cycle("C2", add_days(nowdate(), 5), add_days(nowdate(), 20))

	def test_complete_cycle_transfers(self):
		c1 = self._cycle("C1", add_days(nowdate(), -13), nowdate())
		c2 = self._cycle("C2", add_days(nowdate(), 1), add_days(nowdate(), 14))
		done = self.new_item("Done", cycle=c1.name)
		open_ = self.new_item("Open", cycle=c1.name)
		work_items.update_item(done.name, {"state": self.state("Completed")})
		res = cycles.complete_cycle(c1.name, c2.name)
		self.assertEqual(res["transferred"], 1)
		self.assertEqual(frappe.db.get_value("Runway Work Item", open_.name, "cycle"), c2.name)
		snap = frappe.parse_json(frappe.db.get_value("Runway Cycle", c1.name, "progress_snapshot"))
		self.assertEqual(snap["completed"], 1)
		burndown = cycles.get_burndown(c1.name)
		self.assertEqual(len(burndown["days"]), 14)

	# -------------------------------------------------------------------- intake

	def test_intake_accept_and_decline(self):
		frappe.db.set_value("Runway Project", self.project, "intake_enabled", 1)
		frappe.set_user(MEMBER)
		boot.join_project(self.project)
		req = intake.submit(self.project, "Please add dark mode")
		item = frappe.db.get_value("Runway Intake Item", req, "work_item")
		self.assertEqual(frappe.db.get_value("Runway Work Item", item, "state_group"), "Triage")
		self.assertNotIn(item, [r.name for r in work_items.get_items(project=self.project)])

		frappe.set_user(OWNER)
		intake.accept(req)
		self.assertEqual(frappe.db.get_value("Runway Work Item", item, "state_group"), "Backlog")
		self.assertTrue(frappe.db.exists("Runway Notification", {"for_user": MEMBER, "notification_type": "intake"}))

		req2 = intake.submit(self.project, "Spam")
		intake.decline(req2)
		self.assertEqual(frappe.db.get_value("Runway Intake Item", req2, "status"), "Declined")

	# --------------------------------------------------------------- permissions

	def test_secret_project_hidden_from_non_members(self):
		boot.update_project(self.project, {"network": "Secret"})
		self.new_item("Secret item")
		frappe.set_user(MEMBER)
		clear_access_cache()
		self.assertNotIn(self.project, frappe.get_list("Runway Project", pluck="name"))
		self.assertFalse(frappe.get_list("Runway Work Item", filters={"project": self.project}))
		with self.assertRaises(frappe.PermissionError):
			work_items.get_items(project=self.project)

	def test_outsider_cannot_see_workspace(self):
		frappe.set_user(OUTSIDER)
		clear_access_cache()
		self.assertNotIn(self.ws, frappe.get_list("Runway Workspace", pluck="name"))
		self.assertFalse(boot.get_boot(self.ws).projects)

	def test_public_project_visible_to_workspace_member(self):
		item = self.new_item("Public item")
		frappe.set_user(MEMBER)
		clear_access_cache()
		self.assertIn(item.name, [r.name for r in work_items.get_items(project=self.project)])

	# ----------------------------------------------------------------- analytics

	def test_analytics_by_priority(self):
		self.new_item("a", priority="High")
		self.new_item("b", priority="High")
		self.new_item("c", priority="Low")
		data = get_analytics(project=self.project, x_axis="priority")
		values = {r["key"]: r["value"] for r in data["rows"]}
		self.assertEqual(values, {"High": 2, "Low": 1})
