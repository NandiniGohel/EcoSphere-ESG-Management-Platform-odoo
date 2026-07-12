from odoo import models, fields, api

class EsgCsrActivity(models.Model):
    _name = "esg.csr.activity"
    _description = "ESG CSR Activity"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "activity_date desc, id desc"

    name = fields.Char(string="Activity Title", required=True, tracking=True)
    category_id = fields.Many2one("esg.category", string="Category", domain=[('type', '=', 'csr')], required=True)
    department_id = fields.Many2one("hr.department", string="Sponsoring Department", tracking=True)
    activity_date = fields.Date(string="Start Date", required=True, tracking=True)
    end_date = fields.Date(string="End Date", tracking=True)
    location = fields.Char(string="Location")
    description = fields.Html(string="Description")
    organizer_id = fields.Many2one("hr.employee", string="Organizer", tracking=True)
    max_participants = fields.Integer(string="Max Participants", default=0, help="0 = Unlimited")
    evidence_required = fields.Boolean(
        string="Evidence Required", 
        default=lambda self: self.env['ir.config_parameter'].sudo().get_param('esg.evidence_required_default', False),
        tracking=True
    )
    xp_reward = fields.Integer(string="XP Reward", default=10, help="XP given per participant on completion")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'Open for Registration'),
        ('closed', 'Closed / Finished'),
        ('cancelled', 'Cancelled'),
    ], string="Status", default='draft', tracking=True)

    participation_ids = fields.One2many("esg.employee.participation", "activity_id", string="Participants")
    participant_count = fields.Integer(string="Registered Participants", compute="_compute_participant_counts")
    approved_count = fields.Integer(string="Approved Participations", compute="_compute_participant_counts")

    @api.depends('participation_ids.approval_status')
    def _compute_participant_counts(self):
        for rec in self:
            rec.participant_count = len(rec.participation_ids)
            rec.approved_count = len(rec.participation_ids.filtered(lambda p: p.approval_status == 'approved'))

    def action_open(self):
        self.write({'state': 'open'})

    def action_close(self):
        self.write({'state': 'closed'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_draft(self):
        self.write({'state': 'draft'})
