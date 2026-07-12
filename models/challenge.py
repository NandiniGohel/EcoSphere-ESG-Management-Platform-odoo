from odoo import models, fields, api

class EsgChallenge(models.Model):
    _name = "esg.challenge"
    _description = "ESG Sustainability Challenge"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "end_date desc, id desc"

    name = fields.Char(string="Challenge Title", required=True, tracking=True)
    category_id = fields.Many2one("esg.category", string="Category", domain=[('type', '=', 'challenge')], required=True)
    description = fields.Html(string="Description")
    start_date = fields.Date(string="Start Date", required=True, tracking=True)
    end_date = fields.Date(string="End Date", required=True, tracking=True)
    xp_reward = fields.Integer(string="XP Completion Reward", default=50, tracking=True)
    department_ids = fields.Many2many("hr.department", string="Eligible Departments", help="If empty, all departments are eligible.")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active / In Progress'),
        ('closed', 'Closed'),
    ], string="Status", default='draft', tracking=True)

    target_metric = fields.Selection([
        ('none', 'No specific metric (general activity)'),
        ('co2_reduction', 'Carbon Reduction (kg CO₂e)'),
        ('steps', 'Physical Activity (Steps)'),
        ('energy', 'Energy Savings (kWh)'),
    ], string="Target Metric", required=True, default='none')
    target_value = fields.Float(string="Target Completion Value", default=0.0)
    responsible_id = fields.Many2one("hr.employee", string="Challenge Owner")

    participation_ids = fields.One2many("esg.challenge.participation", "challenge_id", string="Participants")
    participant_count = fields.Integer(string="Participant Count", compute="_compute_participant_counts")
    completion_count = fields.Integer(string="Completion Count", compute="_compute_participant_counts")

    @api.depends('participation_ids.status')
    def _compute_participant_counts(self):
        for rec in self:
            rec.participant_count = len(rec.participation_ids)
            rec.completion_count = len(rec.participation_ids.filtered(lambda p: p.status == 'completed'))

    def action_active(self):
        self.write({'state': 'active'})

    def action_closed(self):
        self.write({'state': 'closed'})

    def action_draft(self):
        self.write({'state': 'draft'})
