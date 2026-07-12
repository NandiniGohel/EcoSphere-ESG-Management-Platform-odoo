from odoo import models, fields, api

class StockMove(models.Model):
    _inherit = 'stock.move'

    emission_factor_id = fields.Many2one('esg.emission.factor', string='Emission Factor')

    def _action_done(self, cancel_backorder=False):
        moves = super(StockMove, self)._action_done(cancel_backorder=cancel_backorder)
        
        # Auto Emission calculation hook
        if self.env['ir.config_parameter'].sudo().get_param('esg.auto_emission_calc', True):
            for move in moves:
                if move.state == 'done' and move.emission_factor_id:
                    # In Odoo 19, quantity moved is quantity or product_qty depending on the flow
                    # Odoo 19 moved quantity field is typically 'quantity' (replaced quantity_done in recent versions)
                    # Let's fallback to product_qty if quantity is zero
                    qty = move.quantity if hasattr(move, 'quantity') else move.product_qty
                    if not qty and hasattr(move, 'product_qty'):
                        qty = move.product_qty
                    self.env['esg.carbon.transaction'].create_from_source(
                        move, 
                        qty, 
                        move.emission_factor_id
                    )
        return moves
