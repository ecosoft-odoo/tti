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
from openerp.tools.translate import _


class purchase_order(osv.osv):

    _inherit = "purchase.order"
    _columns = {
        'past_doc': fields.boolean('Past', readonly=True, states={'draft': [('readonly', False)]})
    }

    def create(self, cr, uid, values, context=None):
        if context.get('past_doc', False):
            values.update({'name': context.get('past_doc_number', False),
                           'past_doc': True})
        return super(purchase_order, self).create(cr, uid, values, context=context)

    def onchange_past_doc(self, cr, uid, ids, past_doc, context=None):
        v = {}
        if past_doc:
            v['name'] = False
        return {'value': v}

    def wkf_confirm_order(self, cr, uid, ids, context=None):
        for po in self.browse(cr, uid, ids, context=context):
            if po.past_doc and po.invoice_method == 'picking':
                raise osv.except_osv(_('Error!'), _('Invoice Control\n"Based on incoming shipment"\nis not allowed for Past Docs!'))
        return super(purchase_order, self).wkf_confirm_order(cr, uid, ids, context=context)

    def _create_pickings(self, cr, uid, order, order_lines, picking_id=False, context=None):
        if not order.past_doc:
            return super(purchase_order, self)._create_pickings(cr, uid, order, order_lines, picking_id=picking_id, context=context)
        else:
            return []

    def action_invoice_create(self, cr, uid, ids, context=None):
        """Assign Past flag from PO to INV
        """
        order = self.browse(cr, uid, ids[0], context=context)
        inv_obj = self.pool.get('account.invoice')
        # create the invoice
        inv_id = super(purchase_order, self).action_invoice_create(cr, uid, ids, context=context)
        # modify the invoice
        inv_obj.write(cr, uid, [inv_id], {'past_doc': order.past_doc})
        return inv_id

purchase_order()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
