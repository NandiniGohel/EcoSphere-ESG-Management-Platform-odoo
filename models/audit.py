from odoo import models, fields, api

class EsgAudit(models.Model):
    _name = "esg.audit"
    _description = "ESG Audit Record"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "audit_date desc, id desc"

    name = fields.Char(string="Audit Reference / Title", required=True, tracking=True)
    audit_type = fields.Selection([
        ('internal', 'Internal Audit'),
        ('external', 'External Audit'),
        ('regulatory', 'Regulatory Audit'),
    ], string="Audit Type", required=True, default='internal', tracking=True)
    category = fields.Selection([
        ('environmental', 'Environmental Pillar'),
        ('social', 'Social Pillar'),
        ('governance', 'Governance Pillar'),
        ('full', 'Full ESG Audit'),
    ], string="Audit Scope", required=True, default='full', tracking=True)
    department_ids = fields.Many2many("hr.department", string="Audited Departments")
    auditor_id = fields.Many2one("res.users", string="Lead Auditor", tracking=True)
    audit_date = fields.Date(string="Audit Date", required=True, tracking=True, default=fields.Date.today)
    completion_date = fields.Date(string="Completion Date", tracking=True)
    state = fields.Selection([
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], string="Status", default='planned', tracking=True)
    
    findings = fields.Html(string="Audit Findings")
    recommendations = fields.Html(string="Recommendations")
    score = fields.Float(string="Audit Score (0-100)", tracking=True)
    
    compliance_issue_ids = fields.One2many("esg.compliance.issue", "audit_id", string="Identified Issues")
    issue_count = fields.Integer(string="Open Issues Count", compute="_compute_issue_count")

    @api.depends('compliance_issue_ids.status')
    def _compute_issue_count(self):
        for rec in self:
            rec.issue_count = len(rec.compliance_issue_ids.filtered(lambda i: i.status in ('open', 'in_progress', 'overdue')))

    def action_start(self):
        self.write({'state': 'in_progress'})

    def action_complete(self):
        self.write({
            'state': 'completed',
            'completion_date': fields.Date.today()
        })

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_draft(self):
        self.write({'state': 'planned'})
