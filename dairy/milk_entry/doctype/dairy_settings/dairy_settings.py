# -*- coding: utf-8 -*-
# Copyright (c) 2019, Dexciss Technology by Sid and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from datetime import date
from datetime import date, timedelta,datetime
from frappe.utils import (flt, getdate, get_url, now,
                          nowtime, get_time, today, get_datetime, add_days, datetime)

class DairySettings(Document):
	# def before_save(self):
	# 	purchase_invoice()
	# 	custom_payment()
	# pass

	@frappe.whitelist()
	def custom_po(self):
		frappe.enqueue(
			method="dairy.milk_entry.doctype.dairy_settings.dairy_settings.custom_payment",
			queue="long",
			timeout=40000
		)

def custom_payment():
	p_inv = frappe.get_doc('Dairy Settings')
	if p_inv.custom_date:
		if p_inv.default_payment_type == 'Daily':
			print('0000000000000000000000000000000000000000000000')
			purchase = frappe.db.sql("""select distinct(supplier) as name 
												from `tabPurchase Receipt` 
												where docstatus =1 and posting_date ='{0}'
												""".format(getdate(today())), as_dict =True)
						
			print('purchase********************************************',purchase)
			for i in purchase:
			# p_inv = frappe.get_doc('Dairy Settings')
			# if p_inv.default_payment_type == 'Daily':
				pi = frappe.new_doc("Purchase Invoice")
				
				
			
				me = frappe.db.sql("""select milk_entry
												from `tabPurchase Receipt` 
												where supplier = '{0}' and posting_date = '{1}' and docstatus = 1
												""".format(i.name,getdate(today())), as_dict =True)
				
				print('meeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee',me)
				for m in me:
					milk = frappe.get_doc('Milk Entry',m.milk_entry)
					print('mmmmmmmmmmmmmmmmmmmmmmmmmmmmmm',m.milk_entry)
					ware = frappe.get_doc('Warehouse',{'name':milk.dcs_id})
					print('ware^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^',ware)

					

					pr =  frappe.db.get_value('Purchase Receipt',{'milk_entry':milk.name,"docstatus":1},['name'])

					# for j in pr:
					if pr:
						pri =  frappe.get_doc('Purchase Receipt',pr)
						pur_inv = frappe.db.get_value('Purchase Invoice Item',{'purchase_receipt':pr},["parent"])
						if not pur_inv:
							
							# pi = frappe.new_doc("Purchase Invoice")
							for itm in pri.items:
								pi.supplier = milk.member if  ware.is_third_party_dcs == 0 else ware.supplier
								pi.milk_entry = milk.name
								pi.set_posting_time = 1
								pi.posting_date = p_inv.custom_date
								pi.append(
									"items",
									{
										'item_code': itm.item_code,
										'item_name': itm.item_name,
										'description': itm.description,
										'received_qty': milk.volume,
										'qty': milk.volume,
										'uom': itm.stock_uom,
										'stock_uom': itm.stock_uom,
										'rate': itm.rate,
										'warehouse': milk.dcs_id,
										'purchase_receipt':pr,
										'fat': itm.fat,
										'snf': itm.clr,
										'snf_clr': itm.snf,
										'fat_per': itm.fat_per_ ,
										'snf_clr_per':itm.clr_per ,
										'snf_per':itm.snf_clr_per,
										'milk_entry':milk.name
									}
								)
				# pi.taxes_and_charges="Deduction Payable"
				# pi.
    
				tax_row = pi.append("taxes", {})
				tax_row.charge_type="On Net Total"
				tax_row.account_head="Deduction Payable - BDF"
				tax_row.category="Total"
				tax_row.add_deduct_tax="Deduct"
				tax_row.description="hi"
				tax_row.rate = 1 
	
				pi.save(ignore_permissions = True)
				pi.submit()
				if (pi.docstatus == 1):
					milk.db_set('status','Billed')



		if p_inv.default_payment_type == 'Days':

			
			n_days_ago = (datetime.datetime.strptime(p_inv.previous_sync_date,'%Y-%m-%d')) + timedelta(days= p_inv.days-1)
			
			purchase = frappe.db.sql("""select distinct(supplier) as name 
											from `tabPurchase Receipt` 
											where docstatus =1 and posting_date BETWEEN '{0}' and '{1}'
											""".format(p_inv.previous_sync_date,getdate(n_days_ago)), as_dict =True)
					
			for i in purchase:
				
				me = frappe.db.sql("""select milk_entry , status , supplier
											from `tabPurchase Receipt` 
											where docstatus= 1 and supplier = '{0}' and posting_date BETWEEN '{1}' and '{2}' and per_billed<100 and milk_entry is not null
											""".format(i.name,p_inv.previous_sync_date,getdate(n_days_ago)), as_dict =True)
				if me:
					pi = frappe.new_doc("Purchase Invoice")
					print('meeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee',me)
					for m in me:
						if m.milk_entry:
							milk = frappe.get_doc('Milk Entry',m.milk_entry)
							ware = frappe.get_doc('Warehouse',{'name':milk.dcs_id})

							pr =  frappe.db.get_value('Purchase Receipt',{'milk_entry':milk.name,"docstatus":1},['name'])
							if pr:
								pri =  frappe.get_doc('Purchase Receipt',pr)

							# if pr:
								# pur_inv = frappe.db.get_value('Purchase Invoice Item',{'purchase_receipt':pr},["parent"])
								# print('pur_inv***************************************',pur_inv)
								# inv = frappe.db.get_value('Purchase Invoice Item',{'purchase_receipt':pr},["pr_detail"])
								# print('inv^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^',inv)
								# if not inv:
								
								# pi = frappe.new_doc("Purchase Invoice")
								pi.supplier = milk.member if  ware.is_third_party_dcs == 0 else ware.supplier
								pi.set_posting_time = 1
								pi.posting_date = p_inv.custom_date
								# pi.milk_entry = milk.name
								for itm in pri.items:
									# pi.supplier = milk.member if  ware.is_third_party_dcs == 0 else ware.supplier
									pi.append(
										"items",
										{
											'item_code': itm.item_code,
											'item_name': itm.item_name,
											'description': itm.description,
											'received_qty': milk.volume,
											'qty': milk.volume,
											'uom': itm.stock_uom,
											'stock_uom': itm.stock_uom,
											'rate': itm.rate,
											'warehouse': milk.dcs_id,
											'purchase_receipt':pr,
											'pr_detail':itm.name,
											'fat': itm.fat,
											'snf': itm.clr,
											'snf_clr': itm.snf,
											'fat_per': itm.fat_per_ ,
											'snf_clr_per':itm.clr_per ,
											'snf_per':itm.snf_clr_per,
											'milk_entry':milk.name
										}
									)
					

					tax_row1 = {
						"charge_type":"Actual",
						"account_head":"Deduction Payable - BDF",
						"category": "Total",
						"add_deduct_tax": "Deduct",
						"description": "Actual",
						"custom_deduction_types": "Bill Wise",
						"rate": 2.0
					}

					pi.append("taxes", tax_row1)

					tax_row2 = {
						"charge_type": "On Item Quantity",
						"account_head": "Deduction Payable - BDF",
						"category": "Total",
						"add_deduct_tax": "Deduct",
						"description": "On Item Quantity",
						"custom_deduction_types": "Litre Wise",
						"rate": 1.0
					}

					pi.append("taxes", tax_row2)

					tax_row3 = {
						"charge_type": "On Net Total",
						"account_head": "Deduction Payable - BDF",
						"category": "Total",
						"add_deduct_tax": "Deduct",
						"description": "On Net Total",
						"custom_deduction_types": "Percentage Wise",
						"rate": 1.0
					}

					pi.append("taxes", tax_row3)



					pi.save(ignore_permissions = True)
					pi.submit()
					if (pi.docstatus == 1):
						milk.db_set('status','Billed')
					frappe.db.commit()
			p_inv.previous_sync_date=getdate(n_days_ago)




		if p_inv.default_payment_type == 'Weekly':
			delta=getdate(today()) - getdate(p_inv.previous_sync_date)
			
			if delta.days >= 7:
				# d2 = getdate(date.today())

				purchase = frappe.db.sql("""select distinct(supplier) as name 
											from `tabPurchase Receipt` 
											where docstatus =1 and posting_date BETWEEN '{0}' and '{1}'
											""".format(p_inv.previous_sync_date,getdate(today())), as_dict =True)
					
			for i in purchase:
				
				me = frappe.db.sql("""select milk_entry , status , supplier
											from `tabPurchase Receipt` 
											where docstatus= 1 and supplier = '{0}' and posting_date BETWEEN '{1}' and '{2}' and per_billed<100
											""".format(i.name,p_inv.previous_sync_date,getdate(today())), as_dict =True)
				if me:
					pi = frappe.new_doc("Purchase Invoice")
					print('meeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee',me)
					for m in me:
						milk = frappe.get_doc('Milk Entry',m.milk_entry)
						ware = frappe.get_doc('Warehouse',{'name':milk.dcs_id})

						pr =  frappe.db.get_value('Purchase Receipt',{'milk_entry':milk.name,"docstatus":1},['name'])
						if pr:
							pri =  frappe.get_doc('Purchase Receipt',pr)

						# if pr:
							# pur_inv = frappe.db.get_value('Purchase Invoice Item',{'purchase_receipt':pr},["parent"])
							# print('pur_inv***************************************',pur_inv)
							# inv = frappe.db.get_value('Purchase Invoice Item',{'purchase_receipt':pr},["pr_detail"])
							# print('inv^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^',inv)
							# if not inv:
							
							# pi = frappe.new_doc("Purchase Invoice")
							pi.supplier = milk.member
							pi.set_posting_time = 1
							pi.posting_date = p_inv.custom_date
							# pi.milk_entry = milk.name
							for itm in pri.items:
								# pi.supplier = milk.member if  ware.is_third_party_dcs == 0 else ware.supplier
								pi.append(
									"items",
									{
										'item_code': itm.item_code,
										'item_name': itm.item_name,
										'description': itm.description,
										'received_qty': milk.volume,
										'qty': milk.volume,
										'uom': itm.stock_uom,
										'stock_uom': itm.stock_uom,
										'rate': itm.rate,
										'warehouse': milk.dcs_id,
										'purchase_receipt':pr,
										'pr_detail':itm.name,
										'fat': itm.fat,
										'snf': itm.clr,
										'snf_clr': itm.snf,
										'fat_per': itm.fat_per_ ,
										'snf_clr_per':itm.clr_per ,
										'snf_per':itm.snf_clr_per,
										'milk_entry':milk.name
									}
								)
					pi.save(ignore_permissions = True)
					pi.submit()
					if (pi.docstatus == 1):
						milk.db_set('status','Billed')
			p_inv.db_set('previous_sync_date',getdate(today()))

		

def purchase_invoice():
	
	# tdate = str(date.today())
	p_inv = frappe.get_doc('Dairy Settings')
	if not p_inv.custom_date:
		if p_inv.default_payment_type == 'Daily':
			print('666666666666666666666666666666666666666666666')
			purchase = frappe.db.sql("""select distinct(supplier) as name 
												from `tabPurchase Receipt` 
												where docstatus =1 and posting_date ='{0}'
												""".format(getdate(today())), as_dict =True)
						
			print('purchase********************************************',purchase)
			for i in purchase:
			# p_inv = frappe.get_doc('Dairy Settings')
			# if p_inv.default_payment_type == 'Daily':
				pi = frappe.new_doc("Purchase Invoice")
				
				
			
				me = frappe.db.sql("""select milk_entry
												from `tabPurchase Receipt` 
												where supplier = '{0}' and posting_date = '{1}' and docstatus = 1
												""".format(i.name,getdate(today())), as_dict =True)
				
				print('meeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee',me)
				for m in me:
					milk = frappe.get_doc('Milk Entry',m.milk_entry)
					print('mmmmmmmmmmmmmmmmmmmmmmmmmmmmmm',m.milk_entry)
					ware = frappe.get_doc('Warehouse',{'name':milk.dcs_id})
					print('ware^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^',ware)

					

					pr =  frappe.db.get_value('Purchase Receipt',{'milk_entry':milk.name,"docstatus":1},['name'])

					# for j in pr:
					if pr:
						pri =  frappe.get_doc('Purchase Receipt',pr)
						pur_inv = frappe.db.get_value('Purchase Invoice Item',{'purchase_receipt':pr},["parent"])
						if not pur_inv:
							
							# pi = frappe.new_doc("Purchase Invoice")
							for itm in pri.items:
								pi.supplier = milk.member if  ware.is_third_party_dcs == 0 else ware.supplier
								pi.milk_entry = milk.name
								pi.append(
									"items",
									{
										'item_code': itm.item_code,
										'item_name': itm.item_name,
										'description': itm.description,
										'received_qty': milk.volume,
										'qty': milk.volume,
										'uom': itm.stock_uom,
										'stock_uom': itm.stock_uom,
										'rate': itm.rate,
										'warehouse': milk.dcs_id,
										'purchase_receipt':pr,
										'fat': itm.fat,
										'snf': itm.clr,
										'snf_clr': itm.snf,
										'fat_per': itm.fat_per_ ,
										'snf_clr_per':itm.clr_per ,
										'snf_per':itm.snf_clr_per,
										'milk_entry':milk.name
									}
								)
				pi.save(ignore_permissions = True)
				pi.submit()
				if (pi.docstatus == 1):
					milk.db_set('status','Billed')



		if p_inv.default_payment_type == 'Days':
			
			n_days_ago = (datetime.datetime.strptime(p_inv.previous_sync_date,'%Y-%m-%d')) + timedelta(days= p_inv.days-1)
				
			purchase = frappe.db.sql("""select distinct(supplier) as name 
											from `tabPurchase Receipt` 
											where docstatus =1 and posting_date BETWEEN '{0}' and '{1}'
											""".format(p_inv.previous_sync_date,getdate(n_days_ago)), as_dict =True)
					
			for i in purchase:
				
				me = frappe.db.sql("""select milk_entry , status , supplier
											from `tabPurchase Receipt` 
											where docstatus= 1 and supplier = '{0}' and posting_date BETWEEN '{1}' and '{2}' and per_billed<100 and milk_entry is not null
											""".format(i.name,p_inv.previous_sync_date,getdate(n_days_ago)), as_dict =True)
				if me:
					pi = frappe.new_doc("Purchase Invoice")
					print('meeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee',me)
					for m in me:
						if m.milk_entry:
							milk = frappe.get_doc('Milk Entry',m.milk_entry)
							ware = frappe.get_doc('Warehouse',{'name':milk.dcs_id})

							pr =  frappe.db.get_value('Purchase Receipt',{'milk_entry':milk.name,"docstatus":1},['name'])
							if pr:
								pri =  frappe.get_doc('Purchase Receipt',pr)

							# if pr:
								# pur_inv = frappe.db.get_value('Purchase Invoice Item',{'purchase_receipt':pr},["parent"])
								# print('pur_inv***************************************',pur_inv)
								# inv = frappe.db.get_value('Purchase Invoice Item',{'purchase_receipt':pr},["pr_detail"])
								# print('inv^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^',inv)
								# if not inv:
								
								# pi = frappe.new_doc("Purchase Invoice")
								pi.supplier = milk.member if  ware.is_third_party_dcs == 0 else ware.supplier
								# pi.milk_entry = milk.name
								for itm in pri.items:
									# pi.supplier = milk.member if  ware.is_third_party_dcs == 0 else ware.supplier
									pi.append(
										"items",
										{
											'item_code': itm.item_code,
											'item_name': itm.item_name,
											'description': itm.description,
											'received_qty': milk.volume,
											'qty': milk.volume,
											'uom': itm.stock_uom,
											'stock_uom': itm.stock_uom,
											'rate': itm.rate,
											'warehouse': milk.dcs_id,
											'purchase_receipt':pr,
											'pr_detail':itm.name,
											'fat': itm.fat,
											'snf': itm.clr,
											'snf_clr': itm.snf,
											'fat_per': itm.fat_per_ ,
											'snf_clr_per':itm.clr_per ,
											'snf_per':itm.snf_clr_per,
											'milk_entry':milk.name
										}
									)
					pi.save(ignore_permissions = True)
					pi.submit()
					if (pi.docstatus == 1):
						milk.db_set('status','Billed')
					frappe.db.commit()
			p_inv.db_set('previous_sync_date',getdate(n_days_ago))




	if p_inv.default_payment_type == 'Weekly':
		delta=getdate(date.today()) - getdate(p_inv.previous_sync_date)
		
		if delta.days >= 7:
			# d2 = getdate(date.today())

			purchase = frappe.db.sql("""select distinct(supplier) as name 
										from `tabPurchase Receipt` 
										where docstatus =1 and posting_date BETWEEN '{0}' and '{1}'
										""".format(p_inv.previous_sync_date,getdate(today())), as_dict =True)
				
		for i in purchase:
			
			me = frappe.db.sql("""select milk_entry , status , supplier
										from `tabPurchase Receipt` 
										where docstatus= 1 and supplier = '{0}' and posting_date BETWEEN '{1}' and '{2}' and per_billed<100
										""".format(i.name,p_inv.previous_sync_date,getdate(today())), as_dict =True)
			if me:
				pi = frappe.new_doc("Purchase Invoice")
				print('meeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee',me)
				for m in me:
					milk = frappe.get_doc('Milk Entry',m.milk_entry)
					ware = frappe.get_doc('Warehouse',{'name':milk.dcs_id})

					pr =  frappe.db.get_value('Purchase Receipt',{'milk_entry':milk.name,"docstatus":1},['name'])
					if pr:
						pri =  frappe.get_doc('Purchase Receipt',pr)

					# if pr:
						# pur_inv = frappe.db.get_value('Purchase Invoice Item',{'purchase_receipt':pr},["parent"])
						# print('pur_inv***************************************',pur_inv)
						# inv = frappe.db.get_value('Purchase Invoice Item',{'purchase_receipt':pr},["pr_detail"])
						# print('inv^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^',inv)
						# if not inv:
						
						# pi = frappe.new_doc("Purchase Invoice")
						pi.supplier = milk.member
						# pi.milk_entry = milk.name
						for itm in pri.items:
							# pi.supplier = milk.member if  ware.is_third_party_dcs == 0 else ware.supplier
							pi.append(
								"items",
								{
									'item_code': itm.item_code,
									'item_name': itm.item_name,
									'description': itm.description,
									'received_qty': milk.volume,
									'qty': milk.volume,
									'uom': itm.stock_uom,
									'stock_uom': itm.stock_uom,
									'rate': itm.rate,
									'warehouse': milk.dcs_id,
									'purchase_receipt':pr,
									'pr_detail':itm.name,
									'fat': itm.fat,
									'snf': itm.clr,
									'snf_clr': itm.snf,
									'fat_per': itm.fat_per_ ,
									'snf_clr_per':itm.clr_per ,
									'snf_per':itm.snf_clr_per,
									'milk_entry':milk.name
								}
							)
				pi.save(ignore_permissions = True)
				pi.submit()
				if (pi.docstatus == 1):
					milk.db_set('status','Billed')
		p_inv.db_set('previous_sync_date',getdate(today()))


