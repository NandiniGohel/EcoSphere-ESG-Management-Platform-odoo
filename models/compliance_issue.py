from odoo import models, fields, api
from datetime import date

class EsgComplianceIssue(models.Model):
    _name = "esg.compliance.issue"
    _description = "ESG Compliance Issue"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "due_date asc, severity desc"

    name = fields.Char(string="Issue Summary", required=True, tracking=True)
    audit_id = fields.Many2one("esg.audit", string="Originating Audit", ondelete="set null")
    department_id = fields.Many2one("hr.department", string="Department", required=True, tracking=True)
    category = fields.Selection([
        ('environmental', 'Environmental'),
        ('social', 'Social'),
        ('governance', 'Governance'),
    ], string="Pillar", required=True, default='governance', tracking=True)
    severity = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ], string="Severity", required=True, default='medium', tracking=True)
    status = fields.Selection([
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('overdue', 'Overdue'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ], string="Status", default='open', required=True, tracking=True)
    due_date = fields.Date(string="Due Date", required=True, tracking=True)
    resolved_date = fields.Date(string="Resolved Date", tracking=True)
    responsible_id = fields.Many2one("hr.employee", string="Responsible Employee", tracking=True)
    description = fields.Html(string="Description")
    resolution_notes = fields.Text(string="Resolution Details")
    is_overdue = fields.Boolean(string="Is Overdue", compute="_compute_is_overdue")

    @api.depends('due_date', 'status')
    def _compute_is_overdue(self):
        today_date = date.today()
        for rec in self:
            if rec.status in ('open', 'in_progress') and rec.due_date and rec.due_date < today_date:
                rec.is_overdue = True
            else:
                rec.is_overdue = False

    def action_resolve(self):
        self.write({
            'status': 'resolved',
            'resolved_date': fields.Date.today()
        })
        self.message_post(body="✅ Compliance issue marked as Resolved.")

    def action_close(self):
        self.write({'status': 'closed'})
        self.message_post(body="🔒 Compliance issue closed.")

    def action_start(self):
        self.write({'status': 'in_progress'})

    @api.model
    def _cron_flag_overdue(self):
        today_date = fields.Date.today()
        overdue_issues = self.search([
            ('status', 'in', ('open', 'in_progress')),
            ('due_date', '<', today_date)
        ])
        for issue in overdue_issues:
            issue.write({'status': 'overdue'})
            # Send notification
            message = f"🚨 Compliance Issue Overdue: <strong>{issue.name}</strong> was due on {issue.due_date}."
            issue.message_post(body=message)
            if issue.responsible_id:
                issue.responsible_id.message_post(body=message)
            if issue.department_id.manager_id:
                issue.department_id.manager_id.message_post(body=message)
