// Copyright (c) 2019, Ridhosribumi and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.ui.form.on('Delivery Note', {
  refresh: function(frm) {
    if (!frm.doc.is_return && frm.doc.status!="Closed") {
      if (frm.doc.docstatus===0) {
        frm.add_custom_button(__('Sales Order'),function() {
            erpnext.utils.map_current_doc({
              method: "erpnext.selling.doctype.sales_order.sales_order.make_delivery_note",
              source_doctype: "Sales Order",
              target: frm,
              setters: {
                customer: frm.doc.customer || undefined,
              },
              get_query_filters: {
                docstatus: 1,
                docstatus_dp: 0,
                status: ["!=", "Closed"],
                per_delivered: ["<", 99.99],
                company: frm.doc.company,
                project: frm.doc.project || undefined,
              }
            })
          }, __("Get items from"));
      }
    }
  },
})
