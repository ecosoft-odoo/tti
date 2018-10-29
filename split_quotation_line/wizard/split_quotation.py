##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, osv
from openerp.tools.translate import _


class PowerDict(dict):
    # http://stackoverflow.com/a/3405143/190597 (gnibbler)
    def __init__(self, parent = None, key = None):
        self.parent = parent
        self.key = key
    def __missing__(self, key):
        self[key] = PowerDict(self, key)
        return self[key]
    def append(self, item):
        self.parent[self.key] = [item]
    def __setitem__(self, key, val):
        dict.__setitem__(self, key, val)
        try:
            val.parent = self
            val.key = key
        except AttributeError:
            pass
        
class split_quotation_confirm(osv.osv_memory):
    _name = "split.quotation.confirm"
    _description = "Split and Merge Quotations"
    _columns = {
        'grouped': fields.boolean('Group the Quotations', help='Check the box to group the quotations for the same customers'),
        'quote_date': fields.date('Quotation Date'),
    }
    _defaults = {
        'grouped': True,
        'quote_date': fields.date.context_today,
    }
 
    def split_quotations(self, cr, uid, ids, context=None):
        
        quote_obj = self.pool.get('sale.order')
        quote_line_obj = self.pool.get('sale.order.line')
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        
        if context is None:
            context = {}
            
        data_confirm = self.read(cr, uid, ids)[0]
        order_line_ids = context.get('active_ids',[])
        
        if not order_line_ids:
            raise osv.except_osv(_('Warning!'), _("You must choose at least one record")) 
        
        #Get the selected quotation no. 
        data_quote_lines = quote_line_obj.read(cr, uid, order_line_ids, ['order_id'], context=context) 
        #Distinct Quotation
        order_ids=list(set([data['order_id'][0] for data in data_quote_lines]))
        
        create_ids = []
        
        
         
        #Create new Quotation
        for order_id in order_ids:
            if quote_line_obj.search_count(cr, uid, [('order_id','=',order_id),('id','not in',order_line_ids)], context=context)>0: 
               
                #**The unselected order line(s)**    
                #Create new Quotation same as selected quotation              
                inv_id = quote_obj.copy(cr, uid, order_id,{'date_order':data_confirm['quote_date'],'order_line':[]}, context)
                #Get sale order line lists are unselected
                orderids_unselected = quote_line_obj.search(cr, uid, [('order_id','=',order_id),('id','not in',order_line_ids)], context=context)
                
                for order_line_id in orderids_unselected:
                    #Create sale order line same as original under new quotation 
                    quote_line_obj.copy(cr, uid, order_line_id,{'order_id': inv_id }, context)                     
                create_ids.append(inv_id)
                
                #**The selected order line(s)** 
                #Create new Quotation same as selected quotation     
                inv_id = quote_obj.copy(cr, uid, order_id,{'date_order':data_confirm['quote_date'],'order_line':[]}, context)
                #Get sale order line lists are selected
                orderids_selected = quote_line_obj.search(cr, uid, [('order_id','=',order_id),('id','in',order_line_ids)], context=context)
                for order_line_id in orderids_selected:
                    #Create sale order line same as original under new quotation
                    quote_line_obj.copy(cr, uid, order_line_id,{'order_id': inv_id }, context)    
                create_ids.append(inv_id)
            else:
                data_quote = quote_obj.read(cr, uid, order_id, ['name'], context=context) 
                raise osv.except_osv(_('Warning!'), _("You can't choose all records on "+ data_quote['name'])) 
        
        #Cancel the selected quotation
        quote_obj.action_cancel( cr, uid, order_ids, context=None)
        
        #Show new Quotation 
        result = mod_obj.get_object_reference(cr, uid, 'sale', 'action_quotations')
        id = result and result[1] or False
        result = act_obj.read(cr, uid, [id], context=context)[0]
        result['domain'] = "[('id','in', [" + ','.join(map(str, create_ids)) + "])]"
         
        return result