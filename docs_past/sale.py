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


class sale_order(osv.osv):

    _inherit = "sale.order"
    _columns = {
        'past_doc': fields.boolean('Past', readonly=True, states={'draft': [('readonly', False)]})
    }

    def create(self, cr, uid, values, context=None):
        if context.get('past_doc', False):
            values.update({'name': context.get('past_doc_number', False),
                           'past_doc': True})
        return super(sale_order, self).create(cr, uid, values, context=context)

    def onchange_past_doc(self, cr, uid, ids, past_doc, context=None):
        v = {}
        if past_doc:
            v['name'] = False
        return {'value': v}

    def action_invoice_create(self, cr, uid, ids, grouped=False, states=None, date_invoice=False, context=None):
        """Assign Past flag from SO to INV
        """
        order = self.browse(cr, uid, ids[0], context=context)
        inv_obj = self.pool.get('account.invoice')
        # create the invoice
        inv_id = super(sale_order, self).action_invoice_create(cr, uid, ids, grouped, states, date_invoice, context=context)
        # modify the invoice
        inv_obj.write(cr, uid, [inv_id], {'past_doc': order.past_doc})
        return inv_id

    def _create_pickings_and_procurements(self, cr, uid, order, order_lines, picking_id=False, context=None):
        """If this is past_doc, do not create pickings
        """
        if not order.past_doc:
            return super(sale_order, self)._create_pickings_and_procurements(cr, uid, order, order_lines, picking_id=picking_id, context=context)
        else:
            return True

sale_order()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
