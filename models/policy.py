from odoo import models, fields, api

class EsgPolicy(models.Model):
    _name = "esg.policy"
    _description = "ESG Governance Policy"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "name"

    name = fields.Char(string="Policy Title", required=True, tracking=True)
    category = fields.Selection([
        ('environmental', 'Environmental'),
        ('social', 'Social'),
        ('governance', 'Governance'),
    ], string="Pillar", required=True, default='governance', tracking=True)
    version = fields.Char(string="Version", default="1.0", tracking=True)
    content = fields.Html(string="Policy Content")
    effective_date = fields.Date(string="Effective Date", tracking=True)
    review_date = fields.Date(string="Review Date", tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('archived', 'Archived'),
    ], string="State", default='draft', tracking=True)
    department_ids = fields.Many2many("hr.department", string="Applicable Departments", help="If empty, applies to all departments.")
    acknowledgement_ids = fields.One2many("esg.policy.acknowledgement", "policy_id", string="Acknowledgements")
    acknowledgement_count = fields.Integer(string="Acknowledgements Count", compute="_compute_acknowledgement_count")
    responsible_id = fields.Many2one("hr.employee", string="Policy Owner", tracking=True)
    attachment_ids = fields.Many2many("ir.attachment", string="Attachments")

    @api.depends('acknowledgement_ids')
    def _compute_acknowledgement_count(self):
        for rec in self:
            rec.acknowledgement_count = len(rec.acknowledgement_ids)

    def action_activate(self):
        self.write({'state': 'active'})
        # Auto-create pending acknowledgements for all employees in applicable departments
        depts = self.department_ids or self.env['hr.department'].search([])
        employees = self.env['hr.employee'].search([('department_id', 'in', depts.ids)])
        ack_model = self.env['esg.policy.acknowledgement']
        for emp in employees:
            existing = ack_model.search([('policy_id', '=', self.id), ('employee_id', '=', emp.id)])
            if not existing:
                ack_model.create({
                    'policy_id': self.id,
                    'employee_id': emp.id,
                    'state': 'pending',
                })

    def action_archive(self):
        self.write({'state': 'archived'})

    def action_draft(self):
        self.write({'state': 'draft'})
