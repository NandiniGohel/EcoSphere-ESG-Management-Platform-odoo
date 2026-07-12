from odoo import models, fields, api, _
from odoo.exceptions import UserError

class EsgEmployeeParticipation(models.Model):
    _name = "esg.employee.participation"
    _description = "Employee CSR Activity Participation"
    _inherit = ['mail.thread']
    _order = "join_date desc, id desc"

    activity_id = fields.Many2one("esg.csr.activity", string="CSR Activity", required=True, ondelete="cascade")
    employee_id = fields.Many2one("hr.employee", string="Employee", required=True, ondelete="cascade")
    department_id = fields.Many2one("hr.department", string="Department", related="employee_id.department_id", store=True, readonly=True)
    join_date = fields.Date(string="Registration Date", default=fields.Date.today, required=True)
    approval_status = fields.Selection([
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string="Approval Status", default='pending', tracking=True)
    evidence_attachment_ids = fields.Many2many("ir.attachment", string="Evidence / Proof Files")
    reviewer_id = fields.Many2one("res.users", string="Reviewer", tracking=True)
    review_date = fields.Date(string="Review Date", tracking=True)
    notes = fields.Text(string="Notes")

    _sql_constraints = [
        ('uniq_activity_employee', 'unique(activity_id, employee_id)', 'This employee is already registered for this CSR activity!'),
    ]

    def action_approve(self):
        for rec in self:
            if rec.approval_status != 'pending':
                continue
                
            # Verify evidence requirement
            if rec.activity_id.evidence_required and not rec.evidence_attachment_ids:
                raise UserError(_("Evidence is required to approve participation for activity '%s'. Please attach a file.") % rec.activity_id.name)
                
            rec.write({
                'approval_status': 'approved',
                'reviewer_id': self.env.user.id,
                'review_date': fields.Date.today(),
            })

            # Create XP transaction
            self.env['esg.xp.transaction'].create({
                'employee_id': rec.employee_id.id,
                'xp_amount': rec.activity_id.xp_reward,
                'transaction_type': 'csr',
                'description': f"Participated in CSR: {rec.activity_id.name}",
                'source_model': rec._name,
                'source_res_id': rec.id,
            })

            # Trigger auto-badge award evaluation
            if self.env['ir.config_parameter'].sudo().get_param('esg.auto_badge_award', True):
                badges = self.env['esg.badge'].search([('active', '=', True)])
                for badge in badges:
                    badge.try_award_badge(rec.employee_id)

    def action_reject(self):
        for rec in self:
            if rec.approval_status != 'pending':
                continue
            rec.write({
                'approval_status': 'rejected',
                'reviewer_id': self.env.user.id,
                'review_date': fields.Date.today(),
            })
