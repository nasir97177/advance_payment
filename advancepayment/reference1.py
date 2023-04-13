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
def get_items_tampungan(related_doc,tipe,percen,company):
    pi_list = []
    item_dp = frappe.get_single('Item Settings').default_item_for_dp
    item_child = frappe.db.sql("""select expense_account from `tabItem Default` where parent =%s and company = %s""",(item_dp,company), as_dict=1)
    item = frappe.db.get_value("Item",item_dp,["item_name","description","stock_uom"], as_dict=1)
    if tipe == "Down Payment":
        po = frappe.db.get_value("Purchase Order",related_doc,["total"], as_dict=1)
    else:
        po = frappe.db.get_value("Purchase Receipt",related_doc,["total"], as_dict=1)
    rate = (flt(percen)/100) * flt(po.total)
    pi_list.append(frappe._dict({
        'item_code': item_dp,
        'item_name': item.item_name,
        'description': item.description,
        'qty': 1,
        'uom': item.stock_uom,
        'rate': rate,
        'amount': rate,
        'expense_account': item_child[0].expense_account
    }))
    return pi_list

@frappe.whitelist()
def get_purchase_invoice(purchase_order, tipe):
    invoice_list = frappe.db.sql("""select purchase_invoice, posting_date, total, net_total from `tabPurchase Order Invoice` where docstatus = '1' and parent = %s order by purchase_invoice asc""", purchase_order, as_dict=True)
    pi_list = []
    for d in invoice_list:
        pi_list.append(frappe._dict({
            'purchase_invoice': d.purchase_invoice,
            'posting_date': d.posting_date,
            'total': d.total,
            'net_total': d.net_total
        }))
    return pi_list

@frappe.whitelist()
def get_purchase_invoice2(purchase_order,delivery,tipe,total):
    if purchase_order != 'none':
        pi_list = []
        invoice_list = frappe.db.sql("""select purchase_invoice,posting_date,total,net_total from `tabPurchase Order Invoice` where docstatus = '1' and parent = %s order by purchase_invoice asc""",purchase_order,as_dict=True)
        for d in invoice_list:
            total_po = frappe.db.sql("""select net_total as so from 'tabPurchase Order' where docstatus = '1' and name = %s""", purchase_order)[0][0]
            total_pi = (flt(total) / flt(total_po)) * flt(d.total)
            net_total = (flt(total) / flt(total_po)) * flt(d.net_total)
            pi_list.append(frappe._dict({
                'purchase_invoice': d.purchase_invoice,
                'posting_date': d.posting_date,
                'total': total_pi,
                'net_total': net_total
            }))
        return pi_list
    if delivery != 'none':
        po = frappe.db.sql("""select distinct(purchase_order) as po from `tabPurchase Receipt Item` where docstatus = '1' and parent = %s """, delivery, as_dict=True)
        for ss in po:
            pi_list = []
            invoice_list = frappe.db.sql("""select purchase_invoice, posting_date, total, net_total from `tabPurchase Order Invoice` where docstatus = '1' and parent = %s order by purchase_invoice asc""", ss.po, as_dict=True)
            for d in invoice_list:
                total_po = frappe.db.sql("""select net_total as po from `tabPurchase Order` where docstatus = '1' and `name` = %s """, ss.po)[0][0]
                total_pi = (flt(total) / flt(total_po)) * flt(d.total)
                net_total = (flt(total) / flt(total_po)) * flt(d.net_total)
                pi_list.append(frappe._dict({
                    'purchase_invoice': d.purchase_invoice,
                    'posting_date': d.posting_date,
                    'total': total_pi,
                    'net_total': net_total
                }))
            return pi_list

@frappe.whitelist()
def get_items_from_pelunasan(purchase_order, total_delivery, percen,company):
    pi_list = []
    item_dp = frappe.get_single('Item Settings').default_item_for_dp
    item_child = frappe.db.sql("""select expense_account from `tabItem Default` where parent =%s and company = %s""",(item_dp,company), as_dict=1)
    item = frappe.db.get_value("Item", item_dp, ["item_name", "description", "stock_uom"], as_dict=1)
    rate = (flt(percen)/100) * flt(total_delivery)
    pi_list.append(frappe._dict({
        'item_code': item_dp,
        'item_name': item.item_name,
        'description': item.description,
        'qty':1,
        'uom': item.stock_uom,
        'rate': rate,
        'amount': rate,
        'expense_account': item_child[0].expense_account
    }))
    return pi_list

@frappe.whitelist()
def get_purchase_receipt(purchase_order):
    if purchase_order:
        pr_list = []
        invoice_list = frappe.db.sql("""select distinct(pr.`name`), pr.posting_date, pr.total, pr.net_total from `tabPurchase Receipt` pr inner join `tabPurchase Receipt Item` pri on pr.`name` = pri.parent where pr.docstatus = '1' and pri.purchase_order = %s""", purchase_order, as_dict=True)
        for d in invoice_list:
            pr_list.append(frappe._dict({
                'purchase_receipt': d.name,
                'posting_date': d.posting_date,
                'total': d.total,
                'net_total': d.net_total
            }))

        return pr_list
