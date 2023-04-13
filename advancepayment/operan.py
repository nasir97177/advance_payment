# -*- coding: utf-8 -*-
# Copyright (c) 2019, Ridhosribumi and contributors
# For license information, please see license.txt
# Ridhosribumi August 2019

from __future__ import unicode_literals
import frappe
from frappe.utils import nowdate, cstr, flt, now, getdate, add_months
from frappe import msgprint, _
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.model.naming import make_autoname
from dateutil import parser
from num2words import num2words
from frappe.utils.background_jobs import enqueue

def submit_sales_order(doc, method):
    enqueue('advancepayment.operan.queue_submit_so', arg1=doc.name)

def cancel_sales_order(doc, method):
    enqueue('advancepayment.operan.queue_delete_so', arg1=doc.name)

def queue_submit_so(arg1):
    write = 0
    so_query = frappe.db.sql("""select `name`, item_code, qty from `tabSales Order Item` where parent = %s""", arg1, as_dict=1)
    for row in so_query:
        for i in range(1,int(row.qty+1)):
            sr = frappe.new_doc("Sales Reversal")
            sr.sales_order = arg1
            sr.so_detail = row.name
            sr.item_code = row.item_code
            sr.save()
            write += 1
            if flt(write) == 100:
                frappe.db.commit()
                write = 0
    frappe.db.commit()

def queue_delete_so(arg1):
    write = 0
    sr_query = frappe.db.sql("""select `name`, qty from `tabSales Reversal` where sales_order = %s""", arg1, as_dict=1)
    for row in sr_query:
        sr = frappe.get_doc("Sales Reversal", row.name)
        sr.delete()
        write += 1
        if flt(write) == 100:
            frappe.db.commit()
            write = 0
    frappe.db.commit()

def submit_sales_invoice(doc, method):
    if doc.type_of_invoice == 'Full Payment':
        frappe.db.set_value("Sales Invoice", doc.name, "sales_order", None)
    elif doc.type_of_invoice == 'Down Payment':
        frappe.db.sql("""update `tabSales Invoice` set delivery_note = null where `name` = %s""", doc.name)
        dataso = frappe.db.sql("""select sum(total_sales_invoice) as jumlah from `tabSales Order` where `docstatus` = 1 and `name` = %s""", doc.sales_order)
        dataso = dataso and dataso[0][0] or 0

        frappe.db.sql("""update `tabSales Order` set total_sales_invoice = %s where name = %s""", (doc.net_total + dataso,doc.sales_order))

        urutan = frappe.db.sql("""select count(*)+1 from `tabSales Order Invoice` where `parent` = %s""",doc.sales_order)[0][0]
        so_invoice = frappe.get_doc({
            "doctype": "Sales Order Invoice",
            "docstatus": 1,
            "parent": doc.sales_order,
            "parentfield": "invoices",
            "parenttype": "Sales Order",
            "sales_invoice": doc.name,
            "posting_date": doc.posting_date,
            "type_of_invoice": doc.type_of_invoice,
            "total": doc.total,
            "net_total": doc.net_total,
            "idx": urutan,
            "percentage": doc.percentage_dp,
            "grand_total": doc.grand_total,
            "total_taxes_and_charges": doc.total_taxes_and_charges
        })
        so_invoice.insert()

        datadpso = frappe.db.sql("""select docstatus_dp from `tabSales Order` where `name` = %s""", doc.sales_order)
        datadpso = datadpso and datadpso[0][0] or 0

        datadpso = datadpso + 1;
        frappe.db.sql("""update `tabSales Order` set docstatus_dp = %s where `name` = %s""", (datadpso,doc.sales_order))
    elif doc.type_of_invoice == 'Progress Payment':
        frappe.db.sql("""update `tabSales Invoice` set sales_order = null where `name` = %s""", doc.name)

        inquiry_list = frappe.db.sql("""select distinct(against_sales_order) from `tabDelivery Note Item` where docstatus = '1' and parent = %s and against_sales_order is not null""", doc.delivery_note, as_dict=True)
        if inquiry_list:
            for ii in inquiry_list:
                urutan = frappe.db.sql("""select max(idx)+1 as tinggi from `tabSales Order Invoice` where `parent` = %s""",ii.against_sales_order)
                urutan = urutan and urutan[0][0] or 0
                dataso = frappe.db.sql("""select sum(total_sales_invoice) as jumlah from `tabSales Order` where `docstatus` = 1 and `name` = %s""", ii.against_sales_order)
                dataso = dataso and dataso[0][0] or 0

                frappe.db.sql("""update `tabSales Order` set total_sales_invoice = %s where name = %s""", (doc.net_total + dataso,ii.against_sales_order))

                so_invoice = frappe.get_doc({
                    "doctype": "Sales Order Invoice",
                    "docstatus": 1,
                    "parent": ii.against_sales_order,
                    "parentfield": "invoices",
                    "parenttype": "Sales Order",
                    "sales_invoice": doc.name,
                    "posting_date": doc.posting_date,
                    "type_of_invoice": doc.type_of_invoice,
                    "total": doc.total,
                    "net_total": doc.net_total,
                    "idx":urutan,
                    "percentage": doc.percentage_dp,
                    "grand_total": doc.grand_total,
                    "total_taxes_and_charges": doc.total_taxes_and_charges
                })
                so_invoice.insert()
    elif doc.type_of_invoice == 'Termin Payment':
        dn = frappe.db.sql("""select delivery_note from `tabSales Invoice DN` where parent = %s""", doc.name, as_dict=1)
        for d in dn:
            frappe.db.sql("""update `tabDelivery Note` set sales_invoice = %s where `name` = %s""", (doc.name, d.delivery_note))
        urutan = frappe.db.sql("""select max(idx)+1 as tinggi from `tabSales Order Invoice` where `parent` = %s""",doc.sales_order)
        urutan = urutan and urutan[0][0] or 0
        dataso = frappe.db.sql("""select sum(total_sales_invoice) as jumlah from `tabSales Order` where `docstatus` = 1 and `name` = %s""", doc.sales_order)
        dataso = dataso and dataso[0][0] or 0

        frappe.db.sql("""update `tabSales Order` set total_sales_invoice = %s where name = %s""", (doc.net_total + dataso,doc.sales_order))

        so_invoice = frappe.get_doc({
            "doctype": "Sales Order Invoice",
            "docstatus": 1,
            "parent": doc.sales_order,
            "parentfield": "invoices",
            "parenttype": "Sales Order",
            "sales_invoice": doc.name,
            "posting_date": doc.posting_date,
            "type_of_invoice": doc.type_of_invoice,
            "total": doc.total,
            "net_total": doc.net_total,
            "idx":urutan,
            "percentage": doc.percentage_dp,
            "grand_total": doc.grand_total,
            "total_taxes_and_charges": doc.total_taxes_and_charges
        })
        so_invoice.insert()
    elif doc.type_of_invoice == 'Retention':
        frappe.db.sql("""update `tabSales Invoice` set delivery_note = null where `name` = %s order by idx""", doc.name)
        dataso = frappe.db.sql("""select sum(total_sales_invoice) as jumlah from `tabSales Order` where `docstatus` = 1 and `name` = %s""", doc.sales_order)
        dataso = dataso and dataso[0][0] or 0

        frappe.db.sql("""update `tabSales Order` set total_sales_invoice = %s where name = %s""", (doc.outstanding_amount + dataso,doc.sales_order))

        urutan = frappe.db.sql("""select max(idx)+1 as tinggi from `tabSales Order Invoice` where `parent` = %s""",doc.sales_order)
        urutan = urutan and urutan[0][0] or 0
        so_invoice = frappe.get_doc({
            "doctype": "Sales Order Invoice",
            "docstatus": 1,
            "parent": doc.sales_order,
            "parentfield": "invoices",
            "parenttype": "Sales Order",
            "sales_invoice": doc.name,
            "posting_date": doc.posting_date,
            "type_of_invoice": doc.type_of_invoice,
            "total": doc.outstanding_amount - doc.total_taxes_and_charges,
            "net_total": doc.outstanding_amount - doc.total_taxes_and_charges,
            "idx":urutan,
            "percentage": (((doc.outstanding_amount - doc.total_taxes_and_charges) / doc.net_total) * 100),
            "grand_total": doc.outstanding_amount - doc.total_taxes_and_charges,
            "total_taxes_and_charges": doc.total_taxes_and_charges
        })
        so_invoice.insert()

def submit_delivery_note(doc, method):
    enqueue('advancepayment.operan.queue_submit_dn', arg1=doc.name)

def cancel_delivery_note(doc, method):
    enqueue('advancepayment.operan.queue_cancel_dn', arg1=doc.name)

def queue_submit_dn(arg1):
    write = 0
    dn_query = frappe.db.sql("""select `name`, so_detail, qty from `tabDelivery Note Item` where parent = %s""", arg1, as_dict=1)
    for row in dn_query:
        if row.so_detail:
            for i in range(1,int(row.qty+1)):
                count_sr = frappe.db.sql("""select count(`name`) from `tabSales Reversal` where so_detail = %s and dn_detail is null order by idx asc""", row.so_detail)[0][0]
                if flt(count_sr) >= 1:
                    sr_name = frappe.db.sql("""select `name` from `tabSales Reversal` where so_detail = %s and dn_detail is null order by idx asc limit 1""", row.so_detail)[0][0]
                    frappe.db.set_value("Sales Reversal", sr_name, "delivery_note", arg1)
                    frappe.db.set_value("Sales Reversal", sr_name, "dn_detail", row.name)
                    write += 1
                    if flt(write) == 100:
                        frappe.db.commit()
                        write = 0
    frappe.db.commit()

def queue_cancel_dn(arg1):
    write = 0
    dn_query = frappe.db.sql("""select `name`, so_detail from `tabSales Reversal` where delivery_note = %s""", arg1, as_dict=1)
    for row in dn_query:
        if row.so_detail:
            frappe.db.sql("""update `tabSales Reversal` set delivery_note = null, dn_detail = null where `name` = %s""", row.name)
            write += 1
            if flt(write) == 100:
                frappe.db.commit()
                write = 0
    frappe.db.commit()

def submit_sales_invoice_2(doc, method):
    if doc.type_of_invoice in ["Down Payment", "Progress Payment"]:
        if doc.get_items_count == 0:
            frappe.throw(_("You must press the <b>Get Items</b> button"))

def submit_sales_invoice_3(doc, method):
    count_qty = frappe.db.sql("""select sum(qty) from `tabSales Invoice Item` where parent = %s""", doc.name)[0][0]
    if flt(count_qty) > 100:
        enqueue('advancepayment.operan.queue_submit_si', arg1=doc.name)
    else:
        for row in doc.items:
            if row.so_detail and row.dn_detail:
                for i in range(1,int(row.qty+1)):
                    count_sr = frappe.db.sql("""select count(`name`) from `tabSales Reversal` where so_detail = %s and dn_detail = %s and si_detail is null order by idx asc""", (row.so_detail, row.dn_detail))[0][0]
                    if flt(count_sr) >= 1:
                        sr_name = frappe.db.sql("""select `name` from `tabSales Reversal` where so_detail = %s and dn_detail = %s and si_detail is null order by idx asc limit 1""", (row.so_detail, row.dn_detail))[0][0]
                        frappe.db.set_value("Sales Reversal", sr_name, "sales_invoice", doc.name)
                        frappe.db.set_value("Sales Reversal", sr_name, "si_detail", row.name)
            elif row.so_detail and not row.dn_detail:
                for i in range(1,int(row.qty+1)):
                    count_sr = frappe.db.sql("""select count(`name`) from `tabSales Reversal` where so_detail = %s and si_detail is null order by idx asc""", row.so_detail)[0][0]
                    if flt(count_sr) >= 1:
                        sr_name = frappe.db.sql("""select `name` from `tabSales Reversal` where so_detail = %s and si_detail is null order by idx asc limit 1""", row.so_detail)[0][0]
                        frappe.db.set_value("Sales Reversal", sr_name, "sales_invoice", doc.name)
                        frappe.db.set_value("Sales Reversal", sr_name, "si_detail", row.name)

def submit_sales_invoice_4(doc, method):
    if doc.type_of_invoice == "Full Payment":
        temp = []
        for row in doc.items:
            if row.sales_order not in temp:
                temp.append(row.sales_order)
        if temp:
            for so in temp:
                if frappe.db.exists("Sales Invoice", {"sales_order":so, "docstatus":1, "type_of_invoice":"Down Payment"}):
                    frappe.throw(_("Sales Order <b>{0}</b> already have Down Payment").format(so))

def check_advanced_payment_amount(doc, method):
    if doc.sales_order and doc.type_of_invoice != "Full Payment":
        adv_payment = frappe.db.get_value("Sales Order", doc.sales_order, "advanced_payment_amount")
        grand_total = frappe.db.get_value("Sales Order", doc.sales_order, "grand_total")
        difference = flt(grand_total) - flt(adv_payment)
        if flt(difference) < (flt(doc.grand_total) - flt(doc.write_off_amount)):
            frappe.throw(_("Nominal is greater than Sales Order"))

def update_sales_order_from_sales_invoice(doc, method):
    if doc.sales_order and doc.type_of_invoice != "Full Payment":
        adv_payment = frappe.db.get_value("Sales Invoice", {"docstatus":1, "sales_order":doc.sales_order}, "sum(grand_total - write_off_amount)") or 0
        frappe.db.set_value("Sales Order", doc.sales_order, "advanced_payment_amount", adv_payment)

def check_advanced_payment_amount_purchase(doc, method):
    if doc.purchase_order and doc.type_of_invoice != "Full Payment":
        adv_payment = frappe.db.get_value("Purchase Order", doc.purchase_order, "advanced_payment_amount")
        grand_total = frappe.db.get_value("Purchase Order", doc.purchase_order, "grand_total")
        difference = flt(grand_total) - flt(adv_payment)
        if flt(difference) < (flt(doc.grand_total) - flt(doc.write_off_amount)):
            frappe.throw(_("Nominal is greater than Purchase Order"))

def update_purchase_order_from_purchase_invoice(doc, method):
    if doc.purchase_order and doc.type_of_invoice != "Full Payment":
        adv_payment = frappe.db.get_value("Purchase Invoice", {"docstatus":1, "purchase_order":doc.purchase_order}, "sum(grand_total - write_off_amount)") or 0
        frappe.db.set_value("Purchase Order", doc.purchase_order, "advanced_payment_amount", adv_payment)

def cancel_sales_invoice(doc, method):
    if doc.type_of_invoice == 'Down Payment':
       frappe.db.sql("""update `tabSales Order` set down_payment = null where `name` = %s""", doc.sales_order)
    elif doc.type_of_invoice == 'Termin Payment':
        dn = frappe.db.sql("""select delivery_note from `tabSales Invoice DN` where parent = %s""", doc.name, as_dict=1)
        for d in dn:
            frappe.db.sql("""update `tabDelivery Note` set sales_invoice = null where `name` = %s""", d.delivery_note)

    frappe.db.sql("""delete from `tabSales Order Invoice` where sales_invoice = %s""", doc.name)

    if doc.type_of_invoice == 'Progress Payment': #or 'Non Project Payment':
       inquiry_list = frappe.db.sql("""select distinct(against_sales_order) from `tabDelivery Note Item` where docstatus = '1' and parent = %s and against_sales_order is not null""", doc.delivery_note)
       inquiry_list = inquiry_list and inquiry_list[0][0] or 0

       dataso = frappe.db.sql("""select sum(net_total) as jumlah from `tabSales Order Invoice` where `docstatus` = 1 and `parent` = %s""", inquiry_list)
       dataso = dataso and dataso[0][0] or 0
       frappe.db.sql("""update `tabSales Order` set total_sales_invoice = %s where name = %s""",(dataso,inquiry_list))

    elif doc.type_of_invoice == 'Down Payment':
       dataso = frappe.db.sql("""select sum(net_total) as jumlah from `tabSales Order Invoice` where `docstatus` = 1 and `parent` = %s""", doc.sales_order)
       dataso = dataso and dataso[0][0] or 0
       frappe.db.sql("""update `tabSales Order` set total_sales_invoice = %s where name = %s""", (dataso,doc.sales_order))

       #status docstatus_dp in sales order
       datadpso = frappe.db.sql("""select docstatus_dp from `tabSales Order` where `name` = %s""", doc.sales_order)
       datadpso = datadpso and datadpso[0][0] or 0
       datadpso = datadpso - 1;
       frappe.db.sql("""update `tabSales Order` set docstatus_dp = %s where `name` = %s""", (datadpso,doc.sales_order))

    elif doc.type_of_invoice == 'Retention':
       dataso = frappe.db.sql("""select sum(net_total) as jumlah from `tabSales Order Invoice` where `docstatus` = 1 and `parent` = %s""", doc.sales_order)
       dataso = dataso and dataso[0][0] or 0
       frappe.db.sql("""update `tabSales Order` set total_sales_invoice = %s where name = %s""", (dataso,doc.sales_order))

    elif doc.type_of_invoice == 'Termin Payment':
       dataso = frappe.db.sql("""select sum(net_total) as jumlah from `tabSales Order Invoice` where `docstatus` = 1 and `parent` = %s""", doc.sales_order)
       dataso = dataso and dataso[0][0] or 0
       frappe.db.sql("""update `tabSales Order` set total_sales_invoice = %s where name = %s""", (dataso,doc.sales_order))

def cancel_sales_invoice_2(doc, method):
    count_qty = frappe.db.sql("""select sum(qty) from `tabSales Invoice Item` where parent = %s""", doc.name)[0][0]
    if flt(count_qty) > 100:
        enqueue('advancepayment.operan.queue_cancel_si', arg1=doc.name)
    else:
        for row in doc.items:
            if row.so_detail:
                frappe.db.sql("""update `tabSales Reversal` set sales_invoice = null, si_detail = null where si_detail = %s""", row.name)
                frappe.db.commit()

def queue_submit_si(arg1):
    write = 0
    si_query = frappe.db.sql("""select `name`, so_detail, dn_detail, qty from `tabSales Invoice Item` where parent = %s""", arg1, as_dict=1)
    for row in si_query:
        if row.so_detail and row.dn_detail:
            for i in range(1,int(row.qty+1)):
                count_sr = frappe.db.sql("""select count(`name`) from `tabSales Reversal` where so_detail = %s and dn_detail = %s and si_detail is null order by idx asc""", (row.so_detail, row.dn_detail))[0][0]
                if flt(count_sr) >= 1:
                    sr_name = frappe.db.sql("""select `name` from `tabSales Reversal` where so_detail = %s and dn_detail = %s and si_detail is null order by idx asc limit 1""", (row.so_detail, row.dn_detail))[0][0]
                    frappe.db.set_value("Sales Reversal", sr_name, "sales_invoice", arg1)
                    frappe.db.set_value("Sales Reversal", sr_name, "si_detail", row.name)
                    write += 1
                    if flt(write) == 100:
                        frappe.db.commit()
                        write = 0
        elif row.so_detail and not row.dn_detail:
            for i in range(1,int(row.qty+1)):
                count_sr = frappe.db.sql("""select count(`name`) from `tabSales Reversal` where so_detail = %s and si_detail is null order by idx asc""", row.so_detail)[0][0]
                if flt(count_sr) >= 1:
                    sr_name = frappe.db.sql("""select `name` from `tabSales Reversal` where so_detail = %s and si_detail is null order by idx asc limit 1""", row.so_detail)[0][0]
                    frappe.db.set_value("Sales Reversal", sr_name, "sales_invoice", arg1)
                    frappe.db.set_value("Sales Reversal", sr_name, "si_detail", row.name)
                    write += 1
                    if flt(write) == 100:
                        frappe.db.commit()
                        write = 0
    frappe.db.commit()

def queue_cancel_si(arg1):
    write = 0
    si_query = frappe.db.sql("""select `name`, so_detail from `tabSales Reversal` where sales_invoice = %s""", arg1, as_dict=1)
    for row in si_query:
        if row.so_detail:
            frappe.db.sql("""update `tabSales Reversal` set sales_invoice = null, si_detail = null where `name` = %s""", row.name)
            write += 1
            if flt(write) == 100:
                frappe.db.commit()
                write = 0
    frappe.db.commit()

def submit_purchase_invoice(doc, method):
    if doc.type_of_invoice == 'Full Payment':
        frappe.db.sql("""update `tabPurchase Invoice` set purchase_order = null where `name` = %s""", doc.name)
    elif doc.type_of_invoice == 'Down Payment':
        frappe.db.sql("""update `tabPurchase Invoice` set purchase_receipt = null where `name` = %s""", doc.name)
        datapo = frappe.db.sql("""select sum(total_purchase_invoice) as jumlah from `tabPurchase Order` where `docstatus` = 1 and `name` = %s""", doc.purchase_order)
        datapo = datapo and datapo[0][0] or 0

        frappe.db.sql("""update `tabPurchase Order` set total_purchase_invoice = %s where name = %s""", (doc.net_total + datapo,doc.purchase_order))

        urutan = frappe.db.sql("""select max(idx)+1 as tinggi from `tabPurchase Order Invoice` where `parent` = %s""",doc.purchase_order)
        urutan = urutan and urutan[0][0] or 0
        po_invoice = frappe.get_doc({
            "doctype": "Purchase Order Invoice",
            "docstatus": 1,
            "parent": doc.purchase_order,
            "parentfield": "invoices",
            "parenttype": "Purchase Order",
            "purchase_invoice": doc.name,
            "posting_date": doc.posting_date,
            "type_of_invoice": doc.type_of_invoice,
            "total": doc.total,
            "net_total": doc.net_total,
            "idx": urutan,
            "percentage": doc.percentage_dp,
            "grand_total": doc.grand_total,
            "total_taxes_and_charges": doc.total_taxes_and_charges
        })
        po_invoice.insert()

        datadppo = frappe.db.sql("""select docstatus_dp from `tabPurchase Order` where `name` = %s""", doc.purchase_order)
        datadppo = datadppo and datadppo[0][0] or 0

        datadppo = datadppo + 1;
        frappe.db.sql("""update `tabPurchase Order` set docstatus_dp = %s where `name` = %s""", (datadppo,doc.purchase_order))

def submit_purchase_invoice_2(doc, method):
    # if doc.type_of_invoice == "Down Payment" or doc.type_of_invoice == "Progress Payment":
    if doc.type_of_invoice in ["Down Payment", "Progress Payment"]:
        if doc.get_items_count == 0:
            frappe.throw(_("You must press the <b>Get Items</b> button"))

def submit_purchase_invoice_3(doc, method):
    if doc.type_of_invoice == "Full Payment":
        temp = []
        for row in doc.items:
            if row.purchase_order not in temp:
                temp.append(row.purchase_order)
        if temp:
            for po in temp:
                if frappe.db.exists("Purchase Invoice", {"purchase_order":po, "docstatus":1, "type_of_invoice":"Down Payment"}):
                    frappe.throw(_("Purchase Order <b>{0}</b> already have Down Payment").format(po))

def cancel_purchase_invoice(doc, method):
    if doc.type_of_invoice == 'Down Payment':
       frappe.db.sql("""update `tabPurchase Order` set down_payment = null where `name` = %s""", doc.purchase_order)
    elif doc.type_of_invoice == 'Termin Payment':
        dn = frappe.db.sql("""select purchase_receipt from `tabPurchase Invoice DN` where parent = %s""", doc.name, as_dict=1)
        for d in dn:
            frappe.db.sql("""update `tabPurchase Receipt` set purchase_invoice = null where `name` = %s""", d.purchase_receipt)

    frappe.db.sql("""delete from `tabPurchase Order Invoice` where purchase_invoice = %s""", doc.name)

    if doc.type_of_invoice == 'Progress Payment': #or 'Non Project Payment':
       inquiry_list = frappe.db.sql("""select distinct(purchase_order) from `tabPurchase Receipt Item` where docstatus = '1' and parent = %s and purchase_order is not null""", doc.purchase_receipt)
       inquiry_list = inquiry_list and inquiry_list[0][0] or 0

       datapo = frappe.db.sql("""select sum(net_total) as jumlah from `tabPurchase Order Invoice` where `docstatus` = 1 and `parent` = %s""", inquiry_list)
       datapo = datapo and datapo[0][0] or 0
       frappe.db.sql("""update `tabPurchase Order` set total_purchase_invoice = %s where name = %s""",(datapo,inquiry_list))

    elif doc.type_of_invoice == 'Down Payment':
       datapo = frappe.db.sql("""select sum(net_total) as jumlah from `tabPurchase Order Invoice` where `docstatus` = 1 and `parent` = %s""", doc.purchase_order)
       datapo = datapo and datapo[0][0] or 0
       frappe.db.sql("""update `tabPurchase Order` set total_purchase_invoice = %s where name = %s""", (datapo,doc.purchase_order))

       #status docstatus_dp in sales order
       datadppo = frappe.db.sql("""select docstatus_dp from `tabPurchase Order` where `name` = %s""", doc.purchase_order)
       datadppo = datadppo and datadppo[0][0] or 0
       datadppo = datadppo - 1;
       frappe.db.sql("""update `tabPurchase Order` set docstatus_dp = %s where `name` = %s""", (datadppo,doc.purchase_order))

    elif doc.type_of_invoice == 'Retention':
       datapo = frappe.db.sql("""select sum(net_total) as jumlah from `tabPurchase Order Invoice` where `docstatus` = 1 and `parent` = %s""", doc.purchase_order)
       datapo = datapo and datapo[0][0] or 0
       frappe.db.sql("""update `tabPurchase Order` set total_purchase_invoice = %s where name = %s""", (datapo,doc.purchase_order))

    elif doc.type_of_invoice == 'Termin Payment':
       datapo = frappe.db.sql("""select sum(net_total) as jumlah from `tabPurchase Order Invoice` where `docstatus` = 1 and `parent` = %s""", doc.purchase_order)
       datapo = datapo and datapo[0][0] or 0
       frappe.db.sql("""update `tabPurchase Order` set total_purchase_invoice = %s where name = %s""", (dataso,doc.purchase_order))

def submit_payment_entry(doc, method):
    if doc.payment_type == 'Receive':
        temp = frappe.db.sql("""select si.sales_order from `tabPayment Entry Reference` pe inner join `tabSales Invoice` si on si.name = pe.reference_name where pe.parent = %s and pe.outstanding_amount = pe.allocated_amount and si.status = 'paid' and pe.docstatus = '1' and si.type_of_invoice = 'Down Payment'""", doc.name);
        for d in temp:
            datadpso = frappe.db.sql("""select docstatus_dp from `tabSales Order` where `name` = %s""", d)
            datadpso = datadpso and datadpso[0][0] or 0
            datadpso = datadpso - 1;
            frappe.db.sql("""update `tabSales Order` set docstatus_dp = %s where `name` = %s""", (datadpso,d))
    elif doc.payment_type == 'Pay':
        temp = frappe.db.sql("""select pi.purchase_order from `tabPayment Entry Reference` pe inner join `tabPurchase Invoice` pi on pi.name = pe.reference_name where pe.parent = %s and pe.outstanding_amount = pe.allocated_amount and pi.status = 'paid' and pe.docstatus = '1' and pi.type_of_invoice = 'Down Payment'""", doc.name);
        for d in temp:
            datadpso = frappe.db.sql("""select docstatus_dp from `tabPurchase Order` where `name` = %s""", d)
            datadpso = datadpso and datadpso[0][0] or 0
            datadpso = datadpso - 1;
            frappe.db.sql("""update `tabPurchase Order` set docstatus_dp = %s where `name` = %s""", (datadpso,d))

def cancel_payment_entry(doc, method):
    if doc.payment_type == 'Receive':
        temp = frappe.db.sql("""select si.sales_order from `tabPayment Entry Reference` pe inner join `tabSales Invoice` si on si.name = pe.reference_name where pe.parent = %s and pe.outstanding_amount = pe.allocated_amount and si.status = 'paid' and pe.docstatus = '1' and si.type_of_invoice = 'Down Payment'""", doc.name);
        for d in temp:
            datadpso = frappe.db.sql("""select docstatus_dp from `tabSales Order` where `name` = %s""", d)
            datadpso = datadpso and datadpso[0][0] or 0
            datadpso = datadpso + 1;
            frappe.db.sql("""update `tabSales Order` set docstatus_dp = %s where `name` = %s""", (datadpso,d))
    elif doc.payment_type == 'Pay':
        temp = frappe.db.sql("""select pi.purchase_order from `tabPayment Entry Reference` pe inner join `tabPurchase Invoice` pi on pi.name = pe.reference_name where pe.parent = %s and pe.outstanding_amount = pe.allocated_amount and pi.status = 'paid' and pe.docstatus = '1' and pi.type_of_invoice = 'Down Payment'""", doc.name);
        for d in temp:
            datadpso = frappe.db.sql("""select docstatus_dp from `tabPurchase Order` where `name` = %s""", d)
            datadpso = datadpso and datadpso[0][0] or 0
            datadpso = datadpso + 1;
            frappe.db.sql("""update `tabPurchase Order` set docstatus_dp = %s where `name` = %s""", (datadpso,d))

def action1():
    query = frappe.db.sql("""select `name` from `tabSales Order` where docstatus = '1'""", as_dict=1)
    for so in query:
        count_sr = frappe.db.sql("""select count(`name`) from `tabSales Reversal` where sales_order = %s""", so.name)[0][0]
        if flt(count_sr) == 0:
            item_query = frappe.db.sql("""select `name`, item_code, qty from `tabSales Order Item` where parent = %s""", so.name, as_dict=1)
            write = 0
            for row in item_query:
                for i in range(1,int(row.qty+1)):
                    sr = frappe.new_doc("Sales Reversal")
                    sr.sales_order = so.name
                    sr.so_detail = row.name
                    sr.item_code = row.item_code
                    sr.flags.ignore_permissions = True
                    sr.save()
                    write += 1
                    if flt(write) == 1000:
                        frappe.db.commit()
                        write = 0
    frappe.db.commit()

def action2():
    write = 0
    query = frappe.db.sql("""select `name` from `tabDelivery Note` where docstatus = '1'""", as_dict=1)
    for dn in query:
        if frappe.db.count("Sales Reversal", {"delivery_note":dn.name}) == 0:
            item_query = frappe.db.sql("""select `name`, so_detail, qty from `tabDelivery Note Item` where parent = %s""", dn.name, as_dict=1)
            for row in item_query:
                if row.so_detail:
                    for i in range(1,int(row.qty+1)):
                        sr_name = frappe.db.sql("""select `name` from `tabSales Reversal` where so_detail = %s and dn_detail is null order by idx asc limit 1""", row.so_detail)[0][0]
                        frappe.db.sql("""update `tabSales Reversal` set delivery_note = %s, dn_detail = %s where `name` = %s""", (dn.name, row.name, sr_name))
                        write += 1
                        if flt(write) == 1000:
                            frappe.db.commit()
                            write = 0
    frappe.db.commit()

def action3():
    write = 0
    query = frappe.db.sql("""select `name` from `tabSales Invoice` where docstatus = '1'""", as_dict=1)
    for si in query:
        if frappe.db.count("Sales Reversal", {"sales_invoice":si.name}) == 0:
            item_query = frappe.db.sql("""select `name`, so_detail, dn_detail, qty from `tabSales Invoice Item` where parent = %s""", si.name, as_dict=1)
            for row in item_query:
                if row.so_detail and row.dn_detail:
                    for i in range(1,int(row.qty+1)):
                        count_sr = frappe.db.sql("""select count(`name`) from `tabSales Reversal` where so_detail = %s and dn_detail = %s and si_detail is null order by idx asc limit 1""", (row.so_detail, row.dn_detail))[0][0]
                        if flt(count_sr) >= 1:
                            sr_name = frappe.db.sql("""select `name` from `tabSales Reversal` where so_detail = %s and dn_detail = %s and si_detail is null order by idx asc limit 1""", (row.so_detail, row.dn_detail))[0][0]
                            frappe.db.set_value("Sales Reversal", sr_name, "sales_invoice", si.name)
                            frappe.db.set_value("Sales Reversal", sr_name, "si_detail", row.name)
                            write += 1
                            if flt(write) == 1000:
                                frappe.db.commit()
                                write = 0
                elif row.so_detail and not row.dn_detail:
                    for i in range(1,int(row.qty+1)):
                        count_sr = frappe.db.sql("""select count(`name`) from `tabSales Reversal` where so_detail = %s and si_detail is null order by idx asc limit 1""", row.so_detail)[0][0]
                        if flt(count_sr) >= 1:
                            sr_name = frappe.db.sql("""select `name` from `tabSales Reversal` where so_detail = %s and si_detail is null order by idx asc limit 1""", row.so_detail)[0][0]
                            frappe.db.set_value("Sales Reversal", sr_name, "sales_invoice", si.name)
                            frappe.db.set_value("Sales Reversal", sr_name, "si_detail", row.name)
                            write += 1
                            if flt(write) == 1000:
                                frappe.db.commit()
                                write = 0
    frappe.db.commit()
