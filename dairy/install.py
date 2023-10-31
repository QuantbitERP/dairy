from __future__ import print_function, unicode_literals
import frappe

def after_install():
    res = frappe.db.sql("""INSERT INTO `tabDomain` (name,domain) VALUES ('Dairy','Dairy')""")
    # res.db_update()