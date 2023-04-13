# -*- coding: utf-8 -*-
# Copyright (c) 2019, Ridhosribumi and contributors
# For license information, please see license.txt
# Ridhosribumi August 2019

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, getdate
from frappe import msgprint, throw, _

def execute(filters=None):
	columns = get_columns()
	data = []

	conditions = get_conditions(filters)
	sl_entries = frappe.db.sql("""select dn.`name`, dn.posting_date, dn.total, (select sum((actual_qty * -1) * valuation_rate) from `tabStock Ledger Entry` where voucher_no = dn.`name`) as hpp from `tabDelivery Note` dn where dn.docstatus = '1' %s and dn.is_return = '0' and dn.status != 'Closed' order by dn.`name` asc""" % conditions, as_dict=1)
	for dn in sl_entries:
		dn_date = dn.posting_date.strftime("%B %Y")
		count_si = frappe.db.sql("""select count(distinct(sales_invoice)) from `tabSales Reversal` where delivery_note = %s""", dn.name)[0][0]

		if flt(count_si) == 0:
			count_jv = frappe.db.get_value("Journal Entry", {"docstatus":1, "delivery_note":dn.name, "reversing_entry":0}, "count(*)")
			if flt(count_jv) != 0:
				je = frappe.db.get_value("Journal Entry", {"delivery_note": dn.name, "reversing_entry": 0, "docstatus": 1}, ["posting_date", "name"], as_dict=1)
				je_name = je.name
				je_date = je.posting_date
			else:
				unicorn = str(dn.name)+"||0||None"
				je_date = """<a href="#Form/Journal Entry/New Journal Entry 1?temp_jv={0}">Make JV</a>""".format(unicorn)
				je_name = ""
			count_rj = frappe.db.get_value("Journal Entry", {"docstatus":1, "delivery_note":dn.name, "reversing_entry":1}, "count(*)")
			if count_rj != 0:
				rj = frappe.db.get_value("Journal Entry", {"delivery_note": dn.name, "reversing_entry": 1, "docstatus": 1}, ["posting_date", "name"], as_dict=1)
				rj_date = rj.posting_date
				rj_name = rj.name
			else:
				rj_date = ""
				rj_name = ""
			check = "-"
			if je_date or rj_date:
				data.append([dn_date, dn.name, dn.total, dn.hpp, '', '', '', '', je_date, je_name, rj_date, rj_name, check])
		else:
			si_query = frappe.db.sql("""select distinct(sales_invoice) as invoice from `tabSales Reversal` where delivery_note = %s""", dn.name, as_dict=1)
			for si in si_query:
				si_date = frappe.db.get_value("Sales Invoice", si.invoice, "posting_date").strftime("%B %Y")
				si_total = frappe.db.get_value("Sales Invoice", si.invoice, "total")
				si_date2 = frappe.db.get_value("Sales Invoice", si.invoice, "posting_date")

				si_cogs = 0
				for r in frappe.db.sql("""select item_code, qty, item_group, warehouse from `tabSales Invoice Item` where parent = %s""", si.invoice, as_dict=1):
					product_bundle = frappe.db.sql("""select count(*) from `tabProduct Bundle` where new_item_code = %s""", r.item_code)[0][0]
					if flt(product_bundle) == 0:
						check_cogs = frappe.db.sql("""select count(*) from `tabStock Ledger Entry` where item_code = %s and posting_date <= %s and warehouse = %s""", (r.item_code, si_date2, r.warehouse))[0][0]
						if flt(check_cogs) >= 1:
							item_cogs = frappe.db.sql("""select valuation_rate from `tabStock Ledger Entry` where item_code = %s and posting_date <= %s and warehouse = %s order by concat_ws(" ", posting_date, posting_time) desc limit 1""", (r.item_code, si_date2, r.warehouse))[0][0]
							si_cogs += flt(item_cogs) * flt(r.qty)
						else:
							check_cogs2 = frappe.db.sql("""select count(*) from `tabStock Ledger Entry` where item_code = %s and posting_date >= %s and warehouse = %s""", (r.item_code, si_date2, r.warehouse))[0][0]
							if flt(check_cogs2) >= 1:
								item_cogs = frappe.db.sql("""select valuation_rate from `tabStock Ledger Entry` where item_code = %s and warehouse = %s order by concat_ws(" ", posting_date, posting_time) desc limit 1""", (r.item_code, r.warehouse))[0][0]
								si_cogs += flt(item_cogs) * flt(r.qty)
							else:
								si_cogs += 0
					else:
						for pb in frappe.db.sql("""select item_code, qty from `tabProduct Bundle Item` where parent = %s""", r.item_code, as_dict=1):
							check_cogs = frappe.db.sql("""select count(*) from `tabStock Ledger Entry` where item_code = %s and posting_date <= %s""", (pb.item_code, si_date2))[0][0]
							if flt(check_cogs) >= 1:
								item_cogs = frappe.db.sql("""select valuation_rate from `tabStock Ledger Entry` where item_code = %s and posting_date <= %s order by concat_ws(" ", posting_date, posting_time) desc limit 1""", (pb.item_code, si_date2))[0][0]
								si_cogs += flt(item_cogs) * flt(pb.qty)
							else:
								check_cogs2 = frappe.db.sql("""select count(*) from `tabStock Ledger Entry` where item_code = %s and posting_date >= %s""", (pb.item_code, si_date2))[0][0]
								if flt(check_cogs2) >= 1:
									item_cogs = frappe.db.sql("""select valuation_rate from `tabStock Ledger Entry` where item_code = %s order by concat_ws(" ", posting_date, posting_time) desc limit 1""", pb.item_code)[0][0]
									si_cogs += flt(item_cogs) * flt(pb.qty)
								else:
									si_cogs += 0

				count_jv = frappe.db.get_value("Journal Entry", {"docstatus":1, "delivery_note":dn.name, "reversing_entry":0}, "count(*)")
				count_jv2 = frappe.db.get_value("Journal Entry", {"docstatus":1, "rss_sales_invoice":si.invoice, "reversing_entry":0}, "count(*)")

				if flt(count_jv) >= 1:
					je = frappe.db.get_value("Journal Entry", {"delivery_note": dn.name, "reversing_entry": 0, "docstatus": 1}, ["posting_date", "name"], as_dict=1)
					je_name = je.name
					je_date = je.posting_date
				elif flt(count_jv2) != 0:
					je = frappe.db.get_value("Journal Entry", {"rss_sales_invoice": si.invoice, "reversing_entry": 0, "docstatus": 1}, ["posting_date", "name"], as_dict=1)
					je_name = je.name
					je_date = je.posting_date
				else:
					unicorn = str(dn.name)+"||0||"+str(si.invoice)
					if dn_date == si_date:
						je_date = ""
					else:
						je_date = """<a href="#Form/Journal Entry/New Journal Entry 1?temp_jv={0}">Make JV</a>""".format(unicorn)
					je_name = ""
				count_rj = frappe.db.get_value("Journal Entry", {"docstatus":1, "delivery_note":dn.name, "reversing_entry":1}, "count(*)")
				count_rj2 = frappe.db.get_value("Journal Entry", {"docstatus":1, "rss_sales_invoice":si.invoice, "reversing_entry":1}, "count(*)")
				if flt(count_rj) != 0:
					rj = frappe.db.get_value("Journal Entry", {"delivery_note": dn.name, "reversing_entry": 1, "docstatus": 1}, ["posting_date", "name"], as_dict=1)
					rj_date = rj.posting_date
					rj_name = rj.name
				elif flt(count_rj2) != 0:
					rj = frappe.db.get_value("Journal Entry", {"rss_sales_invoice": si.invoice, "reversing_entry": 1, "docstatus": 1}, ["posting_date", "name"], as_dict=1)
					rj_date = rj.posting_date
					rj_name = rj.name
				else:
					if dn_date == si_date:
						rj_date = ""
					else:
						unicorn = str(dn.name)+"||1||"+str(si.invoice)
						rj_date = """<a href="#Form/Journal Entry/New Journal Entry 1?temp_jv={0}">Make RJV</a>""".format(unicorn)
					rj_name = ""
				if dn_date == si_date:
					check = "&#10004;"
				elif count_rj != 0:
					check = "&#10004;"
				elif count_rj2 != 0:
					check = "&#10004;"
				else:
					check ="-"
				if je_date or rj_date:
					data.append([dn_date, dn.name, dn.total, dn.hpp, si_date, si.invoice, si_total, si_cogs, je_date, je_name, rj_date, rj_name, check])

	return columns, data

def get_columns():
	"""return columns"""

	columns = [
		_("Tgl DN")+"::100",
		_("No DN")+":Link/Delivery Note:100",
		_("Nilai DN")+":Currency:100",
		_("HPP")+":Currency:100",
		_("Tgl SI")+"::100",
		_("No SI")+":Link/Sales Invoice:100",
		_("Nilai SI")+":Currency:100",
		_("SI Valuation Rate")+":Currency:120",
		_("Tgl JV")+"::100",
		_("No JV")+":Link/Journal Entry:100",
		_("Tgl RJV")+"::100",
		_("No RJV")+":Link/Journal Entry:100",
		_("Check")+"::50",
	]

	return columns

def get_conditions(filters):
	conditions = ""
	if filters.get("from_date"):
		conditions += " and dn.posting_date >= %s" % frappe.db.escape(filters["from_date"])
	if filters.get("to_date"):
		conditions += " and dn.posting_date <= %s" % frappe.db.escape(filters["to_date"])
	if filters.get("month"):
		if filters.get("month") == "Januari":
			month = "01"
		elif filters.get("month") == "Februari":
			month = "02"
		elif filters.get("month") == "Maret":
			month = "03"
		elif filters.get("month") == "April":
			month = "04"
		elif filters.get("month") == "Mei":
			month = "05"
		elif filters.get("month") == "Juni":
			month = "06"
		elif filters.get("month") == "Juli":
			month = "07"
		elif filters.get("month") == "Agustus":
			month = "08"
		elif filters.get("month") == "September":
			month = "09"
		elif filters.get("month") == "Oktober":
			month = "10"
		elif filters.get("month") == "November":
			month = "11"
		elif filters.get("month") == "Desember":
			month = "12"
	yymm = filters.get("year")+"-"+month
	conditions += " and dn.posting_date like '%{0}%'".format(yymm)
	return conditions
