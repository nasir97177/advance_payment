// Copyright (c) 2019, Ridhosribumi and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.ui.form.on('Sales Order', {
  onload: function(frm) {
    if(frm.doc.docstatus == 0 || frm.doc.__islocal){
      frm.clear_table("invoices");
      frm.events.clear(frm);
    }
  },

  clear: function(frm){
     frm.doc.total_sales_invoice = 0;
  },

  set_total_sales_invoice: function(frm){
    var total_si = 0.0;
    $.each(frm.doc.invoices,function(i,row){
      total_si += flt(row.net_total);
    })
    frm.set_value("total_sales_invoice",Math.abs(total_si));
  },
})
