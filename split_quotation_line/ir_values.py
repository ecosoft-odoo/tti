from openerp.osv import osv

class ir_values(osv.osv):
    _inherit = "ir.values"
    
    #Overriding method
    def get_actions(self, cr, uid, action_slot, model, res_id=False, context=None):
        result=super(ir_values,self).get_actions(cr, uid, action_slot, model, res_id, context)
        
        if result and action_slot=='client_action_multi' and context.get('Split_Quote',False):
            tmp_result = []
            for ls in result:
                if ls[1]=='action_split_quotation_line':
                    tmp_result.append(ls)
                    
            result=tmp_result
            
#             if not context.get('Split_Quote',False):
#                 result=result
#             else:
#                 result=[] 
            
        return result