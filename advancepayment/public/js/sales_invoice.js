// Copyright (c) 2019, Ridhosribumi and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.ui.form.on('Sales Invoice', {
	refresh: function(frm){
		frm.events.set_total_delivery_note(frm);
	},
	onload: function(frm){
		frm.set_query("sales_order", function (doc) {
			return {
				filters: {
					'docstatus': 1,
					'status': ["!=", "Completed"],
					'customer': doc.customer
				}
			}
		});
		frm.set_query("delivery_note", function (doc) {
			return {
				filters: {
					'docstatus': 1,
					'status': ["!=", "Completed"],
					'customer': doc.customer
				}
			}
		});
		frm.set_query('delivery_note', 'delivery', function(doc, cdt, cdn) {
			var row = locals[cdt][cdn];
			return {
				filters: {
					'docstatus': 1,
					'status': ["!=", "Completed"],
					'customer': doc.customer
				}
			}
		});
		frm.set_query('sales_invoice', 'related', function(doc, cdt, cdn) {
			var row = locals[cdt][cdn];
			return {
				filters: {
					'docstatus': 1,
					'customer': doc.customer
				}
			}
		});
	},
 	validate: function(frm) {
		frm.events.set_total_delivery_note(frm);
		frm.events.set_total_related_invoice(frm);
		frm.events.validate_percentage(frm);
		frm.events.validate_get_items(frm);
		frm.events.validate_get_items2(frm);
		frm.events.validate_adjustment_tax(frm);
	},
	validate_get_items2: function(frm){
		if(frm.doc.type_of_invoice == "Termin Payment"){
			if(frm.doc.count_get_items2 == 0){
				msgprint("You have not clicked 'Get Items'");
				validated = false;
			}
		}
	},
  validate_percentage: function(frm){
		if(in_list(["Down Payment", "Progress Payment", "Termin Payment"], frm.doc.type_of_invoice)) {
			if(flt(frm.doc.percentage_dp) >= 100 || flt(frm.doc.percentage_dp) <= 0){
				msgprint("Percentage should not be greater than 100 or less than 0");
				validated = false;
			}
		}
	},
	validate_get_items:function(frm){
		if(in_list(["Down Payment", "Progress Payment"], frm.doc.type_of_invoice)) {
			if(frm.doc.get_items_count == 0){
				msgprint("You must press the Get Items button");
				validated = false;
			}
		}
	},
  get_items: function(frm){
    frm.set_value("get_items_count","1");
    frm.clear_table("items");
    if(frm.doc.type_of_invoice == "Down Payment"){
      var jenis = frm.doc.sales_order
		}else if(frm.doc.type_of_invoice == "Progress Payment"){
      var jenis = frm.doc.delivery_note
    }
    return frappe.call({
      method : 'advancepayment.reference.get_items_tampungan',
      args: {
        related_doc: jenis,
        tipe: frm.doc.type_of_invoice,
        percen: frm.doc.percentage_dp,
				company: frm.doc.company
      },
      callback: function(r, rt){
        if(r.message){
          $.each(r.message, function(i,d){
            var c = frm.add_child("items");
            c.item_code = d.item_code;
            c.item_name = d.item_name;
            c.description = d.description;
            c.qty = d.qty;
            c.uom = d.uom;
            c.rate = d.rate;
						c.rate1 = d.rate1;
            c.amount = d.amount;
            c.income_account = d.income_account;
            c.expense_account = d.expense_account;
          })
          frm.refresh_fields();
        }
      }
    })
  },
  type_of_invoice: function(frm){
		if(frm.doc.type_of_invoice == 'Termin Payment'){
  		frm.set_value("count_get_items2","0");
			frm.clear_table("delivery");
			if(!frm.doc.sales_order) return;
			return frappe.call({
				method : 'advancepayment.reference.get_delivery_note',
				args: {
					sales_order: frm.doc.sales_order
				},
				callback: function(r, rt){
					if(r.message){
						$.each(r.message, function(i,d){
							var c = frm.add_child("delivery");
							c.delivery_note = d.delivery_note;
							c.posting_date = d.posting_date;
							c.total = d.total;
							c.net_total = d.net_total;
						})
						frm.refresh_fields();
						frm.events.set_total_delivery_note(frm);
					}
				}
			})
		}else if(frm.doc.type_of_invoice == 'Retention'){
 			frm.clear_table("related");
 			if(!frm.doc.sales_order) return;
 			return frappe.call({
 				method : 'advancepayment.reference.get_sales_invoice',
 				args: {
 					sales_order: frm.doc.sales_order,
 					tipe: frm.doc.type_of_invoice
 				},
 				callback: function(r,rt){
 					if(r.message){
 						$.each(r.message,function(i,d){
 							var c = frm.add_child("related");
 							c.sales_invoice = d.sales_invoice;
							c.status = d.status;
 							c.posting_date = d.posting_date;
 							c.total = d.total;
 							c.net_total = d.net_total;
 						})
 						frm.refresh_fields();
 						frm.events.set_total_related_invoice(frm);
 						frm.events.selling_write_off(frm);
 					}
 				}
 			})
    }else if(frm.doc.type_of_invoice == "Non Project Payment"){
			frm.clear_table("related");
			return frappe.call({
				method: 'advancepayment.reference.get_sales_invoice2',
				args: {
					sales_order: frm.doc.sales_order || "none",
					delivery: frm.doc.delivery_note || "none",
					tipe: frm.doc.type_of_invoice,
					total: frm.doc.net_total
				},
				callback: function(r,rt){
					if(r.message){
						$.each(r.message,function(i,d){
							var c = frm.add_child("related");
							c.sales_invoice = d.sales_invoice;
							c.status = d.status;
							c.posting_date = d.posting_date;
							c.total = d.total;
							c.net_total = d.net_total;
						})
						frm.refresh_fields();
						frm.events.set_total_related_invoice(frm);
						frm.events.selling_write_off(frm);
					}
				}
			})
		}
  },
	selling_write_off: function(frm){
		frappe.call({
			method: "frappe.client.get",
			args: {
				doctype: "Item Settings",
			},
			callback: function(data){
				frm.set_value("write_off_account",data.message.selling_write_off_account);
			}
		})
	},
	set_total_related_invoice: function(frm){
		var total_si = 0.0;
		$.each(frm.doc.related,function(i,row){
			total_si += flt(row.net_total);
		})
		frm.set_value("total_related_invoices",Math.abs(total_si));
		frm.set_value("write_off_amount",Math.abs(total_si));
	},
	set_total_delivery_note: function(frm){
		var total_dn = 0.0;
		$.each(frm.doc.delivery,function(i,row){
			total_dn += flt(row.total);
		})
		frm.set_value("total_delivery_note", Math.abs(total_dn));
	},
	percentage_dp: function(frm){
		frm.events.set_total_delivery_note(frm);
	},
	get_items2: function(frm){
		frm.events.set_total_delivery_note(frm);
		frm.set_value("count_get_items2","1");
		frm.clear_table("items");
		if(!frm.doc.sales_order) return;
		return frappe.call({
			method : 'advancepayment.reference.get_items_from_pelunasan',
			args: {
				sales_order: frm.doc.sales_order,
				total_delivery:frm.doc.total_delivery_note,
				percen: frm.doc.percentage_dp,
				company: frm.doc.company
			},
			callback: function(r,rt){
				if(r.message){
					$.each(r.message,function(i,d){
						var c = frm.add_child("items");
						c.item_code = d.item_code;
						c.item_name = d.item_name;
						c.description = d.description;
						c.qty = d.qty;
						c.uom = d.uom;
						c.rate = d.rate;
						c.amount = d.amount;
						c.income_account = d.income_account;
						c.expense_account = d.expense_account;
					})
					frm.refresh_fields();
				}
			}
		})
	},
	adjust_taxes_and_charges: function(frm, cdt, cdn) {
	  var tbl = frm.doc.taxes || [];
	  var i = tbl.length;
	  while (i--) {
		  if(frm.doc.taxes[i].charge_type != "Actual"){
				frm.doc.taxes[i].print_rate = frm.doc.taxes[i].rate;
				if(frm.doc.taxes[i].included_in_print_rate){
					var tax1 = (flt(frm.doc.taxes[i].rate)/100) * flt(frm.doc.write_off_amount);
				  var tax2 = flt(frm.doc.taxes[i].tax_amount) - tax1;
					var tax3 = flt(frm.doc.total) - tax2;
					var tax4 = tax2/tax3 * 100;
				  frm.doc.taxes[i].rate = tax4;
				}else{
					var selisih = flt(frm.doc.net_total) - flt(frm.doc.write_off_amount);
				  var actual = (flt(frm.doc.taxes[i].rate)/flt(frm.doc.net_total)) * selisih;
				  frm.doc.taxes[i].rate = actual;
				}
			  // frm.doc.taxes[i].charge_type = "Actual";
				// var selisih = flt(frm.doc.net_total) - flt(frm.doc.write_off_amount);
			  // var actual = (flt(frm.doc.taxes[i].tax_amount)/flt(frm.doc.net_total)) * selisih;
			  // frm.doc.taxes[i].tax_amount = Math.round(actual);
			  // frm.doc.taxes[i].charge_type = "Actual";
			  frm.refresh_field("taxes");
		  }
	  }
	  frm.set_value("adjustment_count", "1");
	},
	validate_adjustment_tax: function(frm){
	  if(frm.doc.total_taxes_and_charges != 0){
		  if(frm.doc.type_of_invoice == "Retention" || frm.doc.type_of_invoice == "Non Project Payment"){
			  if(frm.doc.adjustment_count == 0){
				  msgprint("You have not clicked 'Adjust Taxes and Charges'");
				  validated = false;
			  }
		  }
	  }
	},
})
