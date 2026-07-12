from odoo import models, fields, api

class EsgChallengeParticipation(models.Model):
    _name = "esg.challenge.participation"
    _description = "Employee Challenge Participation"
    _inherit = ['mail.thread']
    _order = "enrollment_date desc, id desc"

    challenge_id = fields.Many2one("esg.challenge", string="Challenge", required=True, ondelete="cascade")
    employee_id = fields.Many2one("hr.employee", string="Employee", required=True, ondelete="cascade")
    department_id = fields.Many2one("hr.department", string="Department", related="employee_id.department_id", store=True, readonly=True)
    enrollment_date = fields.Date(string="Enrollment Date", default=fields.Date.today, required=True)
    status = fields.Selection([
        ('enrolled', 'Enrolled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('withdrew', 'Withdrew'),
    ], string="Status", default='enrolled', tracking=True)
    completion_date = fields.Date(string="Completion Date", tracking=True)
    progress_value = fields.Float(string="Progress Reached", default=0.0, tracking=True)
    notes = fields.Text(string="Notes")

    _sql_constraints = [
        ('uniq_challenge_employee', 'unique(challenge_id, employee_id)', 'This employee is already enrolled in this challenge!'),
    ]

    def action_start(self):
        self.write({'status': 'in_progress'})

    def action_complete(self):
        for rec in self:
            if rec.status == 'completed':
                continue
            rec.write({
                'status': 'completed',
                'completion_date': fields.Date.today(),
            })

            # Create XP transaction
            self.env['esg.xp.transaction'].create({
                'employee_id': rec.employee_id.id,
                'xp_amount': rec.challenge_id.xp_reward,
                'transaction_type': 'challenge',
                'description': f"Completed challenge: {rec.challenge_id.name}",
                'source_model': rec._name,
                'source_res_id': rec.id,
            })

            # Trigger auto-badge award evaluation
            if self.env['ir.config_parameter'].sudo().get_param('esg.auto_badge_award', True):
                badges = self.env['esg.badge'].search([('active', '=', True)])
                for badge in badges:
                    badge.try_award_badge(rec.employee_id)

    def action_withdraw(self):
        self.write({'status': 'withdrew'})
