import frappe


def after_install():
	for role in ("Runway User", "Runway Admin"):
		if not frappe.db.exists("Role", role):
			frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 1}).insert(ignore_permissions=True)
	if not frappe.db.exists("Runway Workspace", "default"):
		frappe.get_doc({"doctype": "Runway Workspace", "title": "Default", "slug": "default"}).insert(
			ignore_permissions=True
		)
