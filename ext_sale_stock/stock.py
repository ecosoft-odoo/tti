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

class stock_picking(osv.osv):
    
    _inherit = 'stock.picking'
    _columns = {
        'client_order_ref': fields.related('sale_id', 'client_order_ref', type='char', relation='sale.order', readonly=True, store=False, string='Customer PO'),
    }
     
stock_picking()

class stock_picking_out(osv.osv):
    _inherit = 'stock.picking.out'
    _columns = {
        'client_order_ref': fields.related('sale_id', 'client_order_ref', type='char', relation='sale.order', readonly=True, store=False, string='Customer PO'),
    }
stock_picking_out()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
