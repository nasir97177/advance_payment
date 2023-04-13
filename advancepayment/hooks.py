# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "advancepayment"
app_title = "Advance Payment"
app_publisher = "Ridhosribumi"
app_description = "App for advance payment"
app_icon = "fa fa-newspaper-o"
app_color = "#FFDC00"
app_email = "develop@ridhosribumi.com"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/advancepayment/css/advancepayment.css"
# app_include_js = "/assets/advancepayment/js/advancepayment.js"

# include js, css files in header of web template
# web_include_css = "/assets/advancepayment/css/advancepayment.css"
# web_include_js = "/assets/advancepayment/js/advancepayment.js"

# include js in page
# page_js = {"page" : "public/js/file.js"}
doctype_js = {
	"Sales Invoice": "public/js/sales_invoice.js",
	"Sales Order": "public/js/sales_order.js",
	"Purchase Invoice": "public/js/purchase_invoice.js",
	"Purchase Order": "public/js/purchase_order.js",
	"Delivery Note": "public/js/delivery_note.js",
	"Purchase Receipt": "public/js/purchase_receipt.js",
	"Journal Entry": "public/js/journal_entry.js",
}
# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "advancepayment.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "advancepayment.install.before_install"
# after_install = "advancepayment.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "advancepayment.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
#	}
# }
doc_events = {
	"Sales Order": {
		"on_submit": [
			"advancepayment.operan.submit_sales_order"
		],
		"before_cancel": [
			"advancepayment.operan.cancel_sales_order"
		]
	},
	"Delivery Note": {
		"on_submit": [
			"advancepayment.operan.submit_delivery_note"
		],
		"before_cancel": [
			"advancepayment.operan.cancel_delivery_note"
		]
	},
	"Sales Invoice": {
		"on_submit": [
			"advancepayment.operan.submit_sales_invoice",
			"advancepayment.operan.submit_sales_invoice_2",
			"advancepayment.operan.submit_sales_invoice_3",
			"advancepayment.operan.submit_sales_invoice_4",
            "advancepayment.operan.check_advanced_payment_amount",
            "advancepayment.operan.update_sales_order_from_sales_invoice"
		],
		"before_cancel": [
			"advancepayment.operan.cancel_sales_invoice",
			"advancepayment.operan.cancel_sales_invoice_2"
		],
		"on_cancel": [
            "advancepayment.operan.update_sales_order_from_sales_invoice"
		]
	},
	"Purchase Invoice": {
		"on_submit": [
			"advancepayment.operan.submit_purchase_invoice",
			"advancepayment.operan.submit_purchase_invoice_2",
			"advancepayment.operan.submit_purchase_invoice_3",
            "advancepayment.operan.check_advanced_payment_amount_purchase",
            "advancepayment.operan.update_purchase_order_from_purchase_invoice"
		],
		"before_cancel": [
			"advancepayment.operan.cancel_purchase_invoice",
		],
		"on_cancel": [
            "advancepayment.operan.update_purchase_order_from_purchase_invoice"
		]
	},
	"Payment Entry": {
		"on_submit": [
			"advancepayment.operan.submit_payment_entry",
		],
		"before_cancel": [
			"advancepayment.operan.cancel_payment_entry",
		]
	},
}
# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"advancepayment.tasks.all"
# 	],
# 	"daily": [
# 		"advancepayment.tasks.daily"
# 	],
# 	"hourly": [
# 		"advancepayment.tasks.hourly"
# 	],
# 	"weekly": [
# 		"advancepayment.tasks.weekly"
# 	]
# 	"monthly": [
# 		"advancepayment.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "advancepayment.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "advancepayment.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "advancepayment.task.get_dashboard_data"
# }
