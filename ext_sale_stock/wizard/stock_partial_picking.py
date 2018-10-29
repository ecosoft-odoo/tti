# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-TODAY OpenERP SA (<http://openerp.com>).
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

import time
from lxml import etree
from openerp.osv import fields, osv
from openerp.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools.float_utils import float_compare
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _
from itertools import groupby


# class stock_partial_picking_line(osv.TransientModel):
# 
#     _inherit = "stock.partial.picking.line"
# 
#     def onchange_quantity(self, cr, uid, ids, quantity, move_id, uom, context=None):
#         res = {}
#         uom_obj = self.pool.get('product.uom')
#         uom_data = uom_obj.browse(cr, uid, uom, context=context)
#         if move_id:
#             move_line = self.pool.get('stock.move').browse(cr, uid, move_id, context=context)
#             all_product_line = self.pool.get('stock.move').search
#               
#             if move_line and uom_obj._compute_qty_obj(cr, uid, move_line.product_uom, move_line.product_qty, move_line.product_id.uom_id) < uom_obj._compute_qty_obj(cr, uid, uom_data, quantity, move_line.product_id.uom_id):
#                 res.update({'value': {'quantity': move_line.product_qty, 'product_uom': move_line.product_uom.id}})
#                 res.update({'warning': {'title': 'Over quantity', 'message': 'Quantity can be less than or equal to order but cannot greater than order.'}})
#  
#         return res


class stock_partial_picking(osv.osv_memory):
    _inherit = "stock.partial.picking"

    def do_partial(self, cr, uid, ids, context=None):
        uom_obj = self.pool.get('product.uom')
        partial = self.browse(cr, uid, ids[0], context=context)

        prod_out = {}
        prod_init = {}
        product_ids = []
        for id in ids:
            line_ids = self.pool.get('stock.partial.picking.line').search(cr, uid, [('wizard_id', '=', id)])
            product_ids = [id["product_id"][0] for id in self.pool.get('stock.partial.picking.line').read(cr, uid, line_ids, ['product_id'])]
            product_ids = list(set(product_ids))

        move_ids = self.pool.get('stock.move').search(cr, uid, [('picking_id', '=', partial.picking_id.id), ('product_id', 'in', product_ids)])
        for moveline in self.pool.get('stock.move').browse(cr, uid, move_ids, context=context):
            if prod_init.get(moveline.product_id.id, False):
                prod_init[moveline.product_id.id] += uom_obj._compute_qty_obj(cr, uid, moveline.product_uom, moveline.product_qty, moveline.product_id.uom_id)
            else:
                prod_init.update({moveline.product_id.id: uom_obj._compute_qty_obj(cr, uid, moveline.product_uom, moveline.product_qty, moveline.product_id.uom_id)})

        for wz in partial.move_ids:
            if prod_out.get(wz.product_id.id, False):
                prod_out[wz.product_id.id] += uom_obj._compute_qty_obj(cr, uid, wz.product_uom, wz.quantity, wz.product_id.uom_id)
            else:
                prod_out.update({wz.product_id.id: uom_obj._compute_qty_obj(cr, uid, wz.product_uom, wz.quantity, wz.product_id.uom_id)})

        #Quantiny not over order
        for key in prod_out.keys():
            if prod_out.get(key, False) and prod_init.get(key, False) and prod_out.get(key, False) > prod_init.get(key, False):
                raise osv.except_osv(_('Warning!'), _('Quantity can be less than or equal to order but cannot greater than order.'))

        res = super(stock_partial_picking, self).do_partial(cr, uid, ids, context)
        return res
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
