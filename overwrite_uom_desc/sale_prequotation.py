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


class sale_prequotation(osv.osv):

    _inherit = "sale.prequotation"
    _columns = {
        'overwrite_uom': fields.boolean('Allow overwrite UoM in Quotation', readonly=True, states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]}),
    }

    def write(self, cr, uid, ids, vals, context=None):
        res = super(sale_prequotation, self).write(cr, uid, ids, vals, context=context)
        # Write overwrite_uom flag to SO
        if 'overwrite_uom' in vals:
            order_ids = []
            for pq in self.browse(cr, uid, ids, context=context):
                if pq.mat_sale_id:
                    order_ids.append(pq.mat_sale_id.id)
                if pq.labour_sale_id:
                    order_ids.append(pq.labour_sale_id.id)
            self.pool.get('sale.order').write(cr, uid, order_ids, {'overwrite_uom': vals.get('overwrite_uom')})
        return res

sale_prequotation()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
