# -*- coding: utf-8 -*-
# Copyright (c) 2019, Ridhosribumi and contributors
# For license information, please see license.txt
# Ridhosribumi August 2019

from __future__ import unicode_literals
import frappe, json
from frappe.utils import nowdate, cstr, flt, now, getdate, add_months
from frappe import msgprint, _
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc

@frappe.whitelist()
def get_items_tampungan(related_doc, tipe, percen,company):
    si_list = []
    item_dp = frappe.get_single('Item Settings').default_item_for_dp
    item_child = frappe.db.sql("""select income_account, expense_account from `tabItem Default` where parent =%s and company = %s""",(item_dp,company), as_dict=1)
    item = frappe.db.get_value("Item",item_dp,["item_name","description","stock_uom"], as_dict=1)
    if tipe == "Down Payment":
        so = frappe.db.get_value("Sales Order",related_doc,["total"], as_dict=1)
    else:
        so = frappe.db.get_value("Delivery Note",related_doc,["total"], as_dict=1)
    rate = (flt(percen)/100) * flt(so.total)
    rate_round = round(rate, 0)
    si_list.append(frappe._dict({
        'item_code': item_dp,
        'item_name': item.item_name,
        'description': item.description,
        'qty': 1,
        'uom': item.stock_uom,
        'rate': rate_round,
        'rate1': rate_round,
        'amount': rate_round,
        'income_account': item_child[0].income_account,
        'expense_account': item_child[0].expense_account
    }))
    return si_list

@frappe.whitelist()
def get_sales_invoice(sales_order, tipe):
    invoice_list = frappe.db.sql("""select sales_invoice, posting_date, total, net_total from `tabSales Order Invoice` where docstatus = '1' and parent = %s order by sales_invoice asc""", sales_order, as_dict=True)
    si_list = []
    for d in invoice_list:
        status = frappe.db.get_value("Sales Invoice", d.sales_invoice, "status")
        si_list.append(frappe._dict({
            'sales_invoice': d.sales_invoice,
            'status': status,
            'posting_date': d.posting_date,
            'total': round(d.total, 0),
            'net_total': round(d.net_total, 0)
        }))
    return si_list

@frappe.whitelist()
def get_sales_invoice2(sales_order,delivery,tipe,total):
    if sales_order != 'none':
        si_list = []
        invoice_list = frappe.db.sql("""select sales_invoice, posting_date, total, net_total from `tabSales Order Invoice` where docstatus = '1' and parent = %s order by sales_invoice asc""",sales_order,as_dict=True)
        for d in invoice_list:
            total_so = frappe.db.sql("""select net_total as so from `tabSales Order` where docstatus = '1' and name = %s""", sales_order)[0][0]
            total_si = (flt(total) / flt(total_so)) * flt(d.total)
            net_total = (flt(total) / flt(total_so)) * flt(d.net_total)
            status = frappe.db.get_value("Sales Invoice", d.sales_invoice, "status")
            si_list.append(frappe._dict({
                'sales_invoice': d.sales_invoice,
                'status': status,
                'posting_date': d.posting_date,
                'total': round(total_si, 0),
                'net_total': round(net_total, 0)
            }))
        return si_list
    if delivery != 'none':
        so = frappe.db.sql("""select distinct(against_sales_order) as so from `tabDelivery Note Item` where docstatus = '1' and parent = %s """, delivery, as_dict=True)
        for ss in so:
            si_list = []
            invoice_list = frappe.db.sql("""select sales_invoice, posting_date, total, net_total from `tabSales Order Invoice` where docstatus = '1' and parent = %s order by sales_invoice asc""", ss.so, as_dict=True)
            for d in invoice_list:
                total_so = frappe.db.sql("""select net_total as so from `tabSales Order` where docstatus = '1' and `name` = %s """, ss.so)[0][0]
                total_si = (flt(total) / flt(total_so)) * flt(d.total)
                net_total = (flt(total) / flt(total_so)) * flt(d.net_total)
                si_list.append(frappe._dict({
                    'sales_invoice': d.sales_invoice,
                    'posting_date': d.posting_date,
                    'total': round(total_si, 0),
                    'net_total': round(net_total, 0)
                }))
            return si_list

@frappe.whitelist()
def get_items_from_pelunasan(sales_order, total_delivery, percen,company):
    si_list = []
    item_dp = frappe.get_single('Item Settings').default_item_for_dp
    item_child = frappe.db.sql("""select income_account, expense_account from `tabItem Default` where parent =%s and company = %s""",(item_dp,company), as_dict=1)
    item = frappe.db.get_value("Item", item_dp, ["item_name", "description", "stock_uom"], as_dict=1)
    rate = (flt(percen)/100) * flt(total_delivery)
    si_list.append(frappe._dict({
        'item_code': item_dp,
        'item_name': item.item_name,
        'description': item.description,
        'qty':1,
        'uom': item.stock_uom,
        'rate': rate,
        'amount': rate,
        'income_account': item_child[0].income_account,
        'expense_account': item_child[0].expense_account
    }))
    return si_list

@frappe.whitelist()
def get_delivery_note(sales_order):
    if sales_order:
        dn_list = []
        invoice_list = frappe.db.sql("""select distinct(dn.`name`), dn.posting_date, dn.total, dn.net_total from `tabDelivery Note` dn inner join `tabDelivery Note Item` dni on dn.`name` = dni.parent where dn.docstatus = '1' and dni.against_sales_order = %s""", sales_order, as_dict=True)
        for d in invoice_list:
            dn_list.append(frappe._dict({
                'delivery_note': d.name,
                'posting_date': d.posting_date,
                'total': round(d.total, 0),
                'net_total': round(d.net_total, 0)
            }))

        return dn_list

@frappe.whitelist()
def make_reverse_journal(source_name, target_doc=None):
	def set_missing_values(source, target):
		target.reversing_entry = 1
		target.run_method("set_missing_values")

	jv = get_mapped_doc("Journal Entry", source_name, {
		"Journal Entry": {
			"doctype": "Journal Entry",
    		"field_map":{
    			"posting_date": "posting_date"
    		},
		},
		"Journal Entry Account": {
			"doctype": "Journal Entry Account",
    		"field_map":{
				"credit_in_account_currency": "debit_in_account_currency",
                "debit_in_account_currency": "credit_in_account_currency",
    		},
		},
	}, target_doc, set_missing_values)
	return jv

@frappe.whitelist()
def get_amount_dn(dn, si):
    dn_list = []
    if si != "None":
        inv_date = str(frappe.db.get_value("Sales Invoice", si, "posting_date"))
        invoice_date = "%%%s%%" % str(frappe.db.get_value("Sales Invoice", si, "posting_date"))[:-3]
        invoice_list = frappe.db.sql("""select distinct(sales_order) from `tabSales Invoice Item` where parent = %s""", si, as_dict=True)
        dn_cogs = 0
        for sinv in invoice_list:
            delivery_list = frappe.db.sql("""select dni.`name` as dn_detail from `tabDelivery Note Item` dni, `tabDelivery Note` dn where dn.`name` = dni.parent and dn.docstatus = '1' and dni.against_sales_order = %s and dn.posting_date like %s""", (sinv.sales_order, invoice_date), as_dict=1)
            for dn in delivery_list:
                dn_cogs += frappe.db.get_value("Stock Ledger Entry", {"voucher_detail_no":dn.dn_detail}, "(actual_qty * -1 * valuation_rate)")
        si_cogs = 0
        inv_list = frappe.db.sql("""select * from `tabSales Invoice Item` where parent = %s""", si, as_dict=1)
        for inv in inv_list:
            count_valuation_rate = frappe.db.get_value("Stock Ledger Entry", {"item_code":inv.item_code, "posting_date": ["<=", inv_date], "warehouse":inv.warehouse}, "count(*)")
            if flt(count_valuation_rate) >= 1:
                valuation_rate = frappe.db.sql("""select valuation_rate from `tabStock Ledger Entry` where item_code = %s and posting_date <= %s and warehouse = %s order by concat_ws(" ", posting_date, posting_time) desc limit 1""", (inv.item_code, inv_date, inv.warehouse))[0][0]
            else:
                valuation_rate = 0
            si_cogs += flt(inv.stock_qty) * flt(valuation_rate)
        total_cogs = flt(si_cogs) - flt(dn_cogs)
    else:
        total_cogs = frappe.db.get_value("Stock Ledger Entry", {"voucher_no":dn}, "sum(actual_qty * -1 * valuation_rate)")
    dn_list.append(frappe._dict({
        'debit': flt(total_cogs),
        'credit': ''
    }))
    dn_list.append(frappe._dict({
        'credit': total_cogs,
        'debit': ''
    }))
    return dn_list

@frappe.whitelist()
def make_rjv(dn, si):
    dn_list = []
    if si != "None":
        inv_date = str(frappe.db.get_value("Sales Invoice", si, "posting_date"))
        invoice_date = "%%%s%%" % str(frappe.db.get_value("Sales Invoice", si, "posting_date"))[:-3]
        invoice_list = frappe.db.sql("""select distinct(sales_order) from `tabSales Invoice Item` where parent = %s""", si, as_dict=True)
        dn_cogs = 0
        for sinv in invoice_list:
            delivery_list = frappe.db.sql("""select dni.`name` as dn_detail from `tabDelivery Note Item` dni, `tabDelivery Note` dn where dn.`name` = dni.parent and dn.docstatus = '1' and dni.against_sales_order = %s and dn.posting_date like %s""", (sinv.sales_order, invoice_date), as_dict=1)
            for dn in delivery_list:
                dn_cogs += frappe.db.get_value("Stock Ledger Entry", {"voucher_detail_no":dn.dn_detail}, "(actual_qty * -1 * valuation_rate)")
        si_cogs = 0
        inv_list = frappe.db.sql("""select * from `tabSales Invoice Item` where parent = %s""", si, as_dict=1)
        for inv in inv_list:
            valuation_rate = frappe.db.sql("""select valuation_rate from `tabStock Ledger Entry` where item_code = %s and posting_date <= %s and warehouse = %s order by concat_ws(" ", posting_date, posting_time) desc limit 1""", (inv.item_code, inv_date, inv.warehouse))[0][0]
            si_cogs += flt(inv.stock_qty) * flt(valuation_rate)
        total_cogs = flt(si_cogs) - flt(dn_cogs)
    else:
        total_cogs = frappe.db.get_value("Stock Ledger Entry", {"voucher_no":dn}, "sum(actual_qty * -1 * valuation_rate)")
    dn_list.append(frappe._dict({
        'debit': flt(total_cogs),
        'credit': ''
    }))
    dn_list.append(frappe._dict({
        'credit': total_cogs,
        'debit': ''
    }))
    return dn_list

@frappe.whitelist()
def get_amount_si(si):
    dn_list = []
    si_cogs = frappe.db.get_value("Sales Invoice Item", {"parent":si}, "sum(qty * conversion_factor * cogs)")
    list1 = frappe.db.sql("""select net_total as debit from `tabSales Invoice` where `name` = %s""", si, as_dict=True)
    for d in list1:
        dn_list.append(frappe._dict({
            'party_type': 'Customer',
            'debit': si_cogs,
            'credit': ''
        }))
    list2 = frappe.db.sql("""select net_total as credit from `tabSales Invoice` where `name` = %s""", si, as_dict=True)
    for d in list2:
        dn_list.append(frappe._dict({
            'party_type': 'Customer',
            'debit': '',
            'credit': si_cogs
        }))
    return dn_list
