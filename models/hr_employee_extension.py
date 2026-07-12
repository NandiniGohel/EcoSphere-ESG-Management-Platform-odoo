from odoo import models, fields, api

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    total_xp = fields.Integer(string='Total ESG XP', compute='_compute_total_xp', store=False)
    badge_ids = fields.One2many('esg.employee.badge', 'employee_id', string='Earned Badges')
    badge_count = fields.Integer(string='Badges Count', compute='_compute_badge_count', store=False)
    active_redemption_ids = fields.One2many('esg.reward.redemption', 'employee_id', string='Redemptions')

    def _compute_total_xp(self):
        for employee in self:
            txs = self.env['esg.xp.transaction'].search([('employee_id', '=', employee.id)])
            employee.total_xp = sum(txs.mapped('xp_amount'))

    def _compute_badge_count(self):
        for employee in self:
            employee.badge_count = len(employee.badge_ids)
