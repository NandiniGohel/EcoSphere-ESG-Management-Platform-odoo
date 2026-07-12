from odoo import models, fields, api

class EsgXpTransaction(models.Model):
    _name = "esg.xp.transaction"
    _description = "Employee XP Transaction"
    _order = "date desc, id desc"

    employee_id = fields.Many2one("hr.employee", string="Employee", required=True, ondelete="cascade")
    department_id = fields.Many2one("hr.department", string="Department", related="employee_id.department_id", store=True, readonly=True)
    date = fields.Datetime(string="Date", default=fields.Datetime.now, required=True)
    xp_amount = fields.Integer(string="XP Points", required=True, help="Positive values are earned, negative values are spent.")
    transaction_type = fields.Selection([
        ('csr', 'CSR Activity Participation'),
        ('challenge', 'Challenge Completion'),
        ('badge', 'Badge Reward'),
        ('redemption', 'Reward Redemption'),
        ('manual', 'Manual Adjustment'),
        ('other', 'Other'),
    ], string="Type", required=True, default='manual')
    description = fields.Char(string="Description", required=True)
    source_model = fields.Char(string="Source Model")
    source_res_id = fields.Integer(string="Source Record ID")

    @api.model_create_multi
    def create(self, vals_list):
        records = super(EsgXpTransaction, self).create(vals_list)
        # Check badge unlocks for positive earnings
        if self.env['ir.config_parameter'].sudo().get_param('esg.auto_badge_award', True):
            for rec in records:
                if rec.xp_amount > 0:
                    self._check_badge_awards(rec.employee_id)
        return records

    def _check_badge_awards(self, employee):
        # Find all active badges with XP threshold
        xp_badges = self.env['esg.badge'].search([
            ('active', '=', True),
            ('rule_type', '=', 'xp_threshold')
        ])
        for badge in xp_badges:
            badge.try_award_badge(employee)
