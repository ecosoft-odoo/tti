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


class account_invoice(osv.osv):

    _inherit = 'account.invoice'
    
    _columns = {
        'pq_type': fields.related('sale_order_ids', 'pq_type', type='selection', string='PQ Type', readonly=True,
                                 selection=[
                                    ('trading', 'Trading'),
                                    ('project', 'Project'),
                                    ('calibrate', 'Calibrate'),
                                    ('repair', 'Repair'),
                                    ('rent', 'Rent'),], store=True),
        'overwrite_shipto': fields.text('Overwrite Ship-To'),
        'proforma_number': fields.char('Proforma #', size=32, readonly=True),
    }

    def merge_invoice(self, cr, uid, invoices, context=None):
        """ Check whether ref_sale_order_id is different
        """
        parent = self.pool.get('account.invoice').browse(cr, uid, context['active_id'])
        for inv in invoices:
            if parent.ref_sale_order_id or inv.ref_sale_order_id:
                if parent.ref_sale_order_id != inv.ref_sale_order_id:
                    raise osv.except_osv(_("Ref Sales Order Mismatch!"), _("Can not merge invoice(s) on different Ref Sales Order!."))

        res = super(account_invoice, self).merge_invoice(cr, uid, invoices, context=context)
        return res

    def write(self, cr, uid, ids, vals, context=None):
        if vals.get('state', False) == 'proforma2':
            proforma_number = self.pool.get('ir.sequence').get(cr, uid, 'proforma.invoice')
            vals.update({'proforma_number': proforma_number})
        if vals.get('state', False) == 'cancel':
            vals.update({'proforma_number': False})
        res = super(account_invoice, self).write(cr, uid, ids, vals, context=context)
        return res

account_invoice()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
