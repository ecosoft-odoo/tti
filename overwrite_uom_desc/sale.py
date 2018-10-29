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

from openerp.osv import osv, fields
import openerp.addons.decimal_precision as dp


class sale_order(osv.osv):

    _inherit = "sale.order"
    _columns = {
        'overwrite_uom': fields.boolean('Overwrite UoM Description', readonly=True),
        'order_line_uom': fields.one2many('sale.order.line', 'order_id', 'Order Lines UoM', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}),
    }

sale_order()


class sale_order_line(osv.osv):

    _inherit = 'sale.order.line'
    _columns = {
        'disp_product_uom_qty': fields.float('Display Quantity', digits_compute=dp.get_precision('Product UoS')),
        'disp_uom': fields.char('Display UoM', size=64),
        'disp_price_unit': fields.float('Display Unit Price', digits_compute=dp.get_precision('Product Price')),
    }

sale_order_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
