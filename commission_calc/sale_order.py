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

from osv import fields, osv
from tools.translate import _

class sale_order_team(osv.osv):
    _name = "sale.order.team"

    _columns = {
        'sale_id':fields.many2one('sale.order', 'Sale order', required=False, ondelete='cascade'),
        'sale_team_id':fields.many2one('sale.team', 'Team', required=True),
        'commission_rule_id':fields.many2one('commission.rule', 'Applied Commission', required=True, readonly=True),
    }

    def onchange_sale_team_id(self, cr, uid, ids, sale_team_id):
        result = {}
        res = {}
        if sale_team_id:
            team = self.pool.get('sale.team').browse(cr, uid, sale_team_id)
            res['commission_rule_id'] = team.commission_rule_id.id

        result['value'] = res
        return result
    
sale_order_team()

class sale_order(osv.osv):

    _inherit = "sale.order"
    _columns = {
        'sale_team_ids':fields.one2many('sale.order.team', 'sale_id', 'Teams', states={'draft': [('readonly', False)]})
    }
    
    def _get_sale_team_ids(self, cr, uid, ids, user_id):
        sale_team_ids=[]
        if user_id:
            sale_order_team = self.pool.get('sale.order.team')
            if ids:
                sale_order_team.unlink(cr, uid, sale_order_team.search(cr, uid ,[('sale_id','in',ids)]))
            cr.execute("""select a.tid team_id, b.tid as inherit_id  from sale_team_users_rel a
                            left outer join sale_team_implied_rel b on b.hid = a.tid
                            where uid = %s 
                            """,
                            (user_id,)) 
            team_ids = []
             
            for team_id, inherit_id in cr.fetchall():
                if team_id not in team_ids:
                    team_ids.append(team_id)      
                if inherit_id:
                    if inherit_id not in team_ids:
                        team_ids.append(inherit_id)    
                                                  
                    def _get_all_inherited_team(cr, uid, team_ids, inherit_id):
                        cr.execute("""select tid as interit_id from sale_team_implied_rel
                                    where hid = %s and tid != hid
                                    """,
                                    (inherit_id,))
                        for team_id in cr.fetchall():
                            if team_id[0] not in team_ids:
                                team_ids.append(team_id[0])
                            team_ids = _get_all_inherited_team(cr, uid, team_ids, team_id[0])
                        return team_ids
                    
                    team_ids = _get_all_inherited_team(cr, uid, team_ids, inherit_id)
                    
            teams = self.pool.get('sale.team').browse(cr, uid, team_ids)
            team_recs=[]
            for team in teams:
                team_recs.append({'sale_team_id':team.id,'commission_rule_id':team.commission_rule_id.id})
#                 vals={
#                     'sale_team_id':team.id,
#                     'commission_rule_id':team.commission_rule_id.id,
#                 }
#                 if ids:
#                     for id in ids:
#                         vals['sale_id'] = id
#                 sale_team_id = sale_order_team.create(cr, uid, vals)
#                 sale_team_ids.append(int(sale_team_id))
        
        return team_recs
    
    def onchange_user_id(self, cr, uid, ids, user_id):
        res = {'value':{'sale_team_ids': False}}
        if user_id:
            sale_team_ids = self._get_sale_team_ids(cr, uid, ids, user_id)
            res['value']['sale_team_ids'] =  sale_team_ids
        return res
    
    def create_sale_team(self, cr, uid, ids, context=None):
        sale_recs =  self.browse(cr, uid, ids, context)
        sale_order_team = self.pool.get('sale.order.team')
        sale_teams=[]
        for sale_rec in sale_recs:
            sale_team_ids = self._get_sale_team_ids(cr, uid, [sale_rec.id], sale_rec.user_id.id)
            for sale_value in  sale_team_ids:
 
                sale_value.update({'sale_id':sale_rec.id})
                sale_team_id = sale_order_team.create(cr, uid, sale_value)
                sale_teams.append(sale_team_id) 
        return sale_teams
    
    def create(self, cr, uid, vals, context=None):
        new_id = super(sale_order, self).create(cr, uid, vals, context=context)
        sale_team_ids = self.create_sale_team(cr, uid, [new_id],context)
#         self.write(cr, uid, [new_id], {'sale_team_ids': [(6, 0, sale_team_ids)]})
        return new_id

sale_order()
