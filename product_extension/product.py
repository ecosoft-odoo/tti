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
import re

import netsvc
from osv import osv, fields
from tools.translate import _

class product_template(osv.osv):

    _inherit = "product.template"
    _columns = {
        # Do not translate
        'name': fields.char('Name', size=128, required=True, translate=False, select=True),
    }

product_template()

class product_category(osv.osv):

    _inherit = "product.category"
    _columns = {
        # Do not translate
        'name': fields.char('Name', size=64, required=True, translate=False, select=True),
    }

product_category()

class product_product(osv.osv):

    _inherit = "product.product"

    def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []
        if name:
            # kittiu: For easy default code search
            #ids = self.search(cr, user, [('default_code','=',name)]+ args, limit=limit, context=context)
            ids = self.search(cr, user, [('default_code',operator,name+'%')]+ args, limit=limit, context=context)
            # --kittiu:
            if not ids:
                ids = self.search(cr, user, [('ean13','=',name)]+ args, limit=limit, context=context)
            if not ids:
                # Do not merge the 2 next lines into one single search, SQL search performance would be abysmal
                # on a database with thousands of matching products, due to the huge merge+unique needed for the
                # OR operator (and given the fact that the 'name' lookup results come from the ir.translation table
                # Performing a quick memory merge of ids in Python will give much better performance
                ids = set()
                ids.update(self.search(cr, user, args + [('default_code',operator,name)], limit=limit, context=context))
                if not limit or len(ids) < limit:
                    # we may underrun the limit because of dupes in the results, that's fine
                    # Start kittiu
                    words = name.split(' ')
                    xargs = []
                    for word in words:
                        if len(word.replace(' ','')) > 0:
                            xargs += [('full_name',operator,word.replace(' ',''))]
                    # End kittiu
                    ids = set()
                    # start kittiu
                    #ids.update(self.search(cr, user, args + [('name',operator,name)], limit=(limit and (limit-len(ids)) or False) , context=context))
                    ids.update(self.search(cr, user, args + xargs, limit=(limit and (limit-len(ids)) or False) , context=context))
                    # end kittiu
                ids = list(ids)
            if not ids:
                ptrn = re.compile('(\[(.*?)\])')
                res = ptrn.search(name)
                if res:
                    ids = self.search(cr, user, [('default_code','=', res.group(2))] + args, limit=limit, context=context)
        else:
            ids = self.search(cr, user, args, limit=limit, context=context)
        result = self.name_get(cr, user, ids, context=context)
        return result

    # Overwrite Method
    def name_get(self, cr, user, ids, context=None):
        if context is None:
            context = {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        if not len(ids):
            return []
        def _name_get(d):
            name = d.get('name','')
            code = d.get('default_code',False)
            if code:
                name = '[%s] %s' % (code,name)
            if d.get('variants'):
                name = name + ' - %s' % (d['variants'],)
            # kittiu
            if d.get('attributes'):
                name = name + ' - %s' % (d['attributes'],)
            # -- kittiu
            return (d['id'], name)

        partner_id = context.get('partner_id', False)

        result = []
        for product in self.browse(cr, user, ids, context=context):
            sellers = filter(lambda x: x.name.id == partner_id, product.seller_ids)
            if sellers:
                for s in sellers:
                    mydict = {
                              'id': product.id,
                              'name': s.product_name or product.name,
                              'default_code': s.product_code or product.default_code,
                              'variants': product.variants,
                              # kittiu
                              'attributes': (product.brand_id and product.brand_id.name and ' ' + product.brand_id.name or '') + (product.model and ' ' + product.model or '')
                              # -- kittiu
                              }
                    result.append(_name_get(mydict))
            else:
                mydict = {
                          'id': product.id,
                          'name': product.name,
                          'default_code': product.default_code,
                          'variants': product.variants,
                          # kittiu
                          'attributes': (product.brand_id and product.brand_id.name and ' ' + product.brand_id.name or '') + (product.model and ' ' + product.model or '')

                          # -- kittiu
                          }
                result.append(_name_get(mydict))

        return result


    def _get_full_name(self, cr, uid, ids, name, args, context=None):
        names = self.name_get(cr, uid, ids, context)
        res = {}
        for name in names:
            res[name[0]] = name[1]
        return res

    _columns = {
        'brand_id': fields.many2one('product.brand', 'Brand'),
        'model': fields.char('Model'),
        'full_name': fields.function(_get_full_name, type='char', size=256, string="Full Name",
                store={
                       'product.product': (lambda self, cr, uid, ids, c={}: ids, ['default_code','name', 'brand_id','model'], 20)
                    }),
        'tariff_description': fields.char('Tariff Description'),
        'duty_tax_rate': fields.char('Duty Tax Rate (%)'),

    }
    _defaults = {
        'type': 'product',
    }

product_product()

class product_brand(osv.osv):
    _name = "product.brand"
    _description = "Product Brand"
    _columns = {
        'name': fields.char('Brand Name', size=64, required=False),
        'active': fields.boolean('Active'),
    }
    _defaults = {
        'active': True
    }
product_brand()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
