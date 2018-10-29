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


class account_invoice(osv.osv):

    _inherit = "account.invoice"
    _columns = {
        'overwrite_uom': fields.boolean('Overwrite UoM Description', readonly=True),
        'invoice_line_uom': fields.one2many('account.invoice.line', 'invoice_id', 'Invoice Lines UoM', readonly=True, states={'draft': [('readonly', False)]}),
    }

    def write(self, cr, uid, ids, vals, context=None):
        res = super(account_invoice, self).write(cr, uid, ids, vals, context=context)
        if not isinstance(ids, list):
            ids = [ids]
        for invoice in self.browse(cr, uid, ids, context=context):
            sale = invoice.sale_order_ids and invoice.sale_order_ids[0] or False
            if sale and sale.overwrite_uom:
                cr.execute('update account_invoice set overwrite_uom=%s where id=%s', (sale.overwrite_uom, invoice.id))
        return res

account_invoice()


class account_invoice_line(osv.osv):

    _inherit = 'account.invoice.line'
    _columns = {
        'disp_product_uom_qty': fields.float('Display Quantity', digits_compute=dp.get_precision('Product UoS')),
        'disp_uom': fields.char('Display UoM', size=64),
        'disp_price_unit': fields.float('Display Unit Price', digits_compute=dp.get_precision('Product Price')),
    }

account_invoice_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
