# -*- coding: utf-8 -*-
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

import netsvc
from osv import osv, fields
from openerp.tools.translate import _
import math


class purchase_order(osv.osv):

    _inherit = "purchase.order"

    def _get_quarter_date_order(self, cr, uid, ids, name, args, context=None):
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            str_quarter = False
            if order.date_order:
                str_quarter = "Quarter %s" % (
                    math.ceil(float(int(order.date_order.split('-')[1])) / 3)
                )
            res[order.id] = str_quarter
        return res

    def _get_year_date_order(self, cr, uid, ids, name, args, context=None):
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = order.date_order and order.date_order.split('-')[0] or False
        return res

    _columns = {
        'overwrite_shipto': fields.text('Overwrite Ship-To'),
        'pricelist_id': fields.many2one('product.pricelist', 'Pricelist', change_default=True, required=True, states={'confirmed': [('readonly', True)], 'approved': [('readonly', True)], 'done': [('readonly', True)]}, help="The pricelist sets the currency used for this purchase order. It also computes the supplier price for the selected products/quantities."),
        'quarter_date_order': fields.function(_get_quarter_date_order, type='char', string='Order Date - Quarter',
            store={
                'purchase.order': (lambda self, cr, uid, ids, c={}: ids, [], 4),
                }),        
        'year_date_order': fields.function(_get_year_date_order, type='char', string='Order Date - Year',
            store={
                'purchase.order': (lambda self, cr, uid, ids, c={}: ids, [], 4),
                }),
    }

    def create(self, cr, uid, data, context=None):
        # Search for default note, if not specified
        if not data.get('notes', False):
            ir_values = self.pool.get('ir.values')
            condition = 'pricelist_id=' + str(data.get('pricelist_id', False))
            notes = ir_values.get_default(cr, uid, 'purchase.order', 'notes', for_all_users=True, company_id=data.get('company_id', False), condition=condition)
            data.update({'notes': notes})
        result = super(purchase_order, self).create(cr, uid, data, context=context)
        return result

purchase_order()


class purchase_order_line(osv.osv):

    _inherit = 'purchase.order.line'
    _order = 'sequence, id'
    _columns = {
        'sequence': fields.integer('Sequence', help="Gives the sequence order when displaying a list of purchase order lines."),
    }
    _defaults = {
        'sequence': 1000,
    }

purchase_order_line()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
