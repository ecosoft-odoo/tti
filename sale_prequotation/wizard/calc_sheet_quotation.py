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

from openerp.osv import fields, osv
from openerp.tools.translate import _


class calcsheet_quotation(osv.osv_memory):
    _name = "calcsheet.quotation"
    _description = "Calculation Sheet to Quotations"

    _columns = {
        'can_split': fields.boolean('Can Split'),
        'split': fields.boolean('Split Material and Labour'),
        'type': fields.selection([
                ('list', 'List'),
                ('bundle', 'Bundle')], string='Type', required=True, readonly=False),
    }
    _defaults = {
        'can_split': lambda self,cr,uid,c: (c.get('order_line', False) and c.get('order_line_labour', False)) and True or False 
    }

    def create_quotation(self, cr, uid, ids, context=None):
        if not context:
            return
        pq_ids = context.get('active_ids', False)
        res = {}
        if not pq_ids:
            return
        pq_obj = self.pool.get('sale.prequotation')
        for pq in pq_obj.browse(cr, uid, pq_ids, context):
            if not (pq.order_line_labour or pq.order_line):
                raise osv.except_osv(_('Warning!'), _("Please select Product(s)"))

            for this in self.browse(cr, uid, ids, context=context):
                if not pq.project_name and this.type == 'bundle':
                    raise osv.except_osv(_('Warning!'), _("Please input Product/Project Name in Calculation Sheet"))

                if this.split:
                    res = pq_obj.action_split_quotion(cr, uid, pq_ids, this.type, context)
                else:
                    res = pq_obj.action_sale(cr, uid, pq_ids, this.type, context)

        return res

calcsheet_quotation()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
