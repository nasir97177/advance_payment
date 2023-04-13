// Copyright (c) 2019, Ridhosribumi and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.ui.form.on('Purchase Receipt', {
  refresh: function(frm) {
    if (!frm.doc.is_return && frm.doc.status!="Closed") {
			if (frm.doc.docstatus == 0) {
				frm.add_custom_button(__('Purchase Order'),
					function () {
						erpnext.utils.map_current_doc({
							method: "erpnext.buying.doctype.purchase_order.purchase_order.make_purchase_receipt",
							source_doctype: "Purchase Order",
							target: frm,
							setters: {
								supplier: frm.doc.supplier || undefined,
							},
							get_query_filters: {
								docstatus: 1,
                docstatus_dp: 0,
								status: ["!=", "Closed"],
								per_received: ["<", 99.99],
								company: frm.doc.company
							}
						})
					}, __("Get items from"));
			}
    }
  },
})
