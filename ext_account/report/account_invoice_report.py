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

from openerp import tools
import openerp.addons.decimal_precision as dp
from openerp.osv import fields,osv

class account_invoice_report(osv.osv):
    _inherit = "account.invoice.report"

    _columns = {
        'brand_id': fields.many2one('product.brand', 'Brand', readonly=True),
        'sale_order_id': fields.many2one('sale.order', 'Sales Order', readonly=True),        
        'pq_type': fields.selection([
                            ('trading', 'Trading'),
                            ('project', 'Project'),
                            ('calibrate', 'Calibrate'),
                            ('repair', 'Repair'),
                            ('rent', 'Rent'),
                            ], 'PQ Type', readonly=True,),

    }

    def _select(self):
        return  super(account_invoice_report, self)._select() + ", sale_order_id, brand_id, pq_type"

    def _sub_select(self):
        return  super(account_invoice_report, self)._sub_select() + ", soiv.order_id as sale_order_id, br.id as brand_id, ai.pq_type"

    def _from(self):
        return super(account_invoice_report, self)._from() + " left join product_brand br on br.id = pr.brand_id left join sale_order_invoice_rel soiv on soiv.invoice_id = ai.id "

    def _group_by(self):
        return super(account_invoice_report, self)._group_by() + ", soiv.order_id, br.id, ai.pq_type"

account_invoice_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
