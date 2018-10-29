#!/usr/bin/python
"""
:The login function is under
::    http://localhost:5069/xmlrpc/common
:For object retrieval use:
::    http://localhost:5069/xmlrpc/object
"""
import xmlrpclib

user = 'admin'
pwd = 'mia'
dbname = 'TT_IMPORT'

 

sock = xmlrpclib.ServerProxy('http://localhost:5069/xmlrpc/common')
uid = sock.login(dbname ,user ,pwd)
pwd = 'mia'
sock = xmlrpclib.ServerProxy('http://localhost:5069/xmlrpc/object')

# # CREATE A PARTNER
# partner_data = {'name'.. code-block:: php:'Tiny', 'active':True, 'vat':'ZZZZZ'}
# partner_id = sock.execute(dbname, uid, pwd, model, 'create', partner_data)
# 
# # The relation between res.partner and res.partner.category is of type many2many
# # To add  categories to a partner use the following format:
# partner_data = {'name':'Provider2', 'category_id': [(6,0,[3, 2, 1])]}
# # Where [3, 2, 1] are id fields of lines in res.partner.category
# 
# # SEARCH PARTNERS
# args = []
# ids = sock.execute(dbname, uid, pwd, model, 'search', args)
# 
# # # READ PARTNER DATA
# # fields = ['name', 'active', 'vat', 'ref']
# # results = sock.execute(dbname, uid, pwd, model, 'read', ids, fields)
# # print results
# # 
# # # EDIT PARTNER DATA
# # values = {'vat':'ZZ1ZZ'}
# # results = sock.execute(dbname, uid, pwd, model, 'write', ids, values)
# 
#Delete product
model = 'product.product'
args = [('brand_id','=',12)]
ids = sock.execute(dbname, uid, pwd, model, 'search', args)
print "product Deleting..."
results = sock.execute(dbname, uid, pwd, model, 'unlink', ids)
#   
# #Delete Supplier
# model = 'res.partner'
# args = [('supplier', '=', True),]
# ids = sock.execute(dbname, uid, pwd, model, 'search', args)
# print "Supplier Deleting...." 
# results = sock.execute(dbname, uid, pwd, model, 'unlink', ids)
# 
# #Delete customer
# model = 'res.partner'
# args = [('customer', '=', True),]
# ids = sock.execute(dbname, uid, pwd, model, 'search', args)
# print "Customer Deleting...." 
# results = sock.execute(dbname, uid, pwd, model, 'unlink', ids)
# 
# #product.category
# model = 'product.category'
# args = [('name', '!=', 'All products'),('name', '!=', 'Saleable')]
# ids = sock.execute(dbname, uid, pwd, model, 'search', args)
# print "Product Category Deleting...." 
# results = sock.execute(dbname, uid, pwd, model, 'unlink', ids)
