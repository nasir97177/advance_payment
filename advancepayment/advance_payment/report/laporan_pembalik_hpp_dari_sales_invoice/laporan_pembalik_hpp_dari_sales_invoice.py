# -*- coding: utf-8 -*-
# Copyright (c) 2019, Ridhosribumi and contributors
# For license information, please see license.txt
# Ridhosribumi August 2019

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, getdate

def execute(filters=None):
	columns = get_columns()
	data = []

	conditions = get_conditions(filters)
	sl_entries = frappe.db.sql("""select distinct(si.`name`), si.posting_date, si.net_total, sii.sales_order from `tabSales Invoice` si inner join `tabSales Invoice Item` sii on si.`name` = sii.parent where si.docstatus = '1' and sii.sales_order is not null %s order by si.posting_date asc""" % conditions, as_dict=1)
	for ri in sl_entries:
		check_dn = frappe.db.sql("""select count(*) from `tabDelivery Note Item` where against_sales_order = %s""", ri.sales_order)[0][0]
		if flt(check_dn) == 0:
			si_date = ri.posting_date.strftime("%B %Y")
			count_jv = frappe.db.sql("""select count(*) from `tabJournal Entry` where rss_sales_invoice = %s and docstatus = '1' and reversing_entry = '0'""", ri.name)[0][0]
			if flt(count_jv) != 0:
				jv = frappe.db.get_value("Journal Entry", {"rss_sales_invoice": ri.name, "reversing_entry": 0, "docstatus": 1}, ["posting_date", "name"], as_dict=1)
				make_jv = jv.name
				jv_date = jv.posting_date.strftime("%B %Y")
			else:
				make_jv = "<a href='/desk#Form/Journal%20Entry/New%20Journal%20Entry%201?rss_sales_invoice="+ri.name+"'>Make JV</a>"
				jv_date = ""
			data.append([si_date, ri.name, ri.net_total, make_jv, jv_date])

	return columns, data

def get_columns():
	"""return columns"""

	columns = [
		_("Tgl SI")+"::100",
		_("No SI")+":Link/Sales Invoice:100",
		_("Nilai SI")+":Currency:100",
		_("Journal Voucher")+":Link/Journal Entry:100",
		_("Tgl JV")+"::100",
	]

	return columns

def get_conditions(filters):
	conditions = ""
	if filters.get("from_date"):
		conditions += " and si.posting_date >= %s" % frappe.db.escape(filters["from_date"])
	if filters.get("to_date"):
		conditions += " and si.posting_date <= %s" % frappe.db.escape(filters["to_date"])
	return conditions
