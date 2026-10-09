import frappe


def project_payload(project: dict, role: str) -> dict:
	"""A project with the lookups every work item screen needs."""
	name = project["name"]
	p = frappe._dict(
		{
			k: project.get(k)
			for k in (
				"name",
				"workspace",
				"title",
				"identifier",
				"description",
				"emoji",
				"color",
				"lead",
				"default_assignee",
				"network",
				"estimate",
				"archived",
				"cycles_enabled",
				"modules_enabled",
				"views_enabled",
				"intake_enabled",
			)
		}
	)
	p.role = role
	p.states = frappe.get_all(
		"Runway State",
		filters={"project": name},
		fields=["name", "title", "state_group", "color", "sequence", "is_default", "description"],
		order_by="sequence asc",
	)
	p.labels = frappe.get_all(
		"Runway Label",
		filters={"project": name},
		fields=["name", "title", "color", "parent_label"],
		order_by="title asc",
	)
	p.members = frappe.db.sql(
		"""select m.user, m.role, u.full_name, u.user_image
		from `tabRunway Project Member` m join `tabUser` u on u.name = m.user
		where m.project = %s order by u.full_name""",
		name,
		as_dict=True,
	)
	p.estimate_type = None
	p.estimate_points = []
	if p.estimate:
		p.estimate_type = frappe.db.get_value("Runway Estimate", p.estimate, "estimate_type")
		p.estimate_points = frappe.get_all(
			"Runway Estimate Point",
			filters={"parent": p.estimate, "parenttype": "Runway Estimate"},
			pluck="value",
			order_by="idx asc",
		)
	p.cycles = frappe.get_all(
		"Runway Cycle",
		filters={"project": name},
		fields=["name", "title", "status", "start_date", "end_date", "completed_at"],
		order_by="start_date desc",
	)
	p.modules = frappe.get_all(
		"Runway Module",
		filters={"project": name},
		fields=["name", "title", "status"],
		order_by="title asc",
	)
	return p
