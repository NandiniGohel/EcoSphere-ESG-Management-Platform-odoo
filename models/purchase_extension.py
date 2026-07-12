from odoo import models, fields, api

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def button_confirm(self):
        res = super(PurchaseOrder, self).button_confirm()
        
        # Auto Emission calculation hook
        if self.env['ir.config_parameter'].sudo().get_param('esg.auto_emission_calc', True):
            for order in self:
                for line in order.order_line:
                    if line.emission_factor_id:
                        self.env['esg.carbon.transaction'].create_from_source(
                            line, 
                            line.product_qty, 
                            line.emission_factor_id
                        )
        return res

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    emission_factor_id = fields.Many2one('esg.emission.factor', string='Emission Factor')
