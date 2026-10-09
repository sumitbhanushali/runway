import frappe

from runway.api.cycles import _points, progress
from runway.api.work_items import query_items
from runway.utils import check_project_access


@frappe.whitelist()
def get_modules(project: str):
	check_project_access(project)
	points = _points(project)
	modules = frappe.get_all("Runway Module", filters={"project": project}, fields=["*"], order_by="creation desc")
	members = frappe.get_all(
		"Runway Module Member",
		filters={"parenttype": "Runway Module", "parent": ("in", [m.name for m in modules] or [""])},
		fields=["parent", "user"],
	)
	items = query_items(project=project, filters={"modules": [m.name for m in modules] or [""]})
	for m in modules:
		m.members = [x.user for x in members if x.parent == m.name]
		m.progress = progress([i for i in items if m.name in i.modules], points)
	return modules


@frappe.whitelist()
def get_module(name: str):
	doc = frappe.get_doc("Runway Module", name)
	doc.check_permission("read")
	out = doc.as_dict()
	points = _points(doc.project)
	out.progress = progress(query_items(project=doc.project, filters={"modules": [name]}), points)
	return out
