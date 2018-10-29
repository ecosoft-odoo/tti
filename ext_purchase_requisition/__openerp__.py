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

{
    'name' : "Extensions for Purchase Requisition",
    'author' : 'Ecosoft',
    'summary': '',
    'description': """
Features
========

* Get price list from supplier
* Add new field 'Calculation Sheet number'
* Get the SO number when user select Calc Sheet
  * If Calc Sheet have 2 SO, leave it blank.

""",
    'category': 'Purchase Management',
    'sequence': 8,
    'website' : 'http://www.ecosoft.co.th',
    'images' : [],
    'depends' : ['web_m2x_options',
                 'purchase_requisition',
                 'purchase_requisition_double_validation',
                 'purchase_requisition_multi_supplier',
                 'sale_prequotation',
                 'job_cost_sheet'],
    'demo' : [],
    'data' : [
        'purchase_requisition_view.xml',

    ],
    'test' : [
    ],
    'auto_install': False,
    'application': True,
    'installable': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
