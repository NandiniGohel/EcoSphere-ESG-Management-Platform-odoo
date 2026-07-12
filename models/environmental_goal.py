from odoo import models, fields, api

class EsgEnvironmentalGoal(models.Model):
    _name = "esg.environmental.goal"
    _description = "ESG Environmental Goal"
    _order = "end_date desc, id desc"

    name = fields.Char(string="Goal Name", required=True)
    department_id = fields.Many2one("hr.department", string="Department", required=True)
    goal_type = fields.Selection([
        ('carbon_reduction', 'Carbon Reduction'),
        ('energy_saving', 'Energy Saving'),
        ('waste_reduction', 'Waste Reduction'),
        ('water_saving', 'Water Saving'),
        ('other', 'Other'),
    ], string="Goal Type", required=True, default='carbon_reduction')
    target_value = fields.Float(string="Target Value", required=True)
    current_value = fields.Float(string="Current Value", default=0.0)
    unit = fields.Char(string="Unit", required=True, help="e.g. tCO2e, kWh, Litres")
    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('achieved', 'Achieved'),
        ('missed', 'Missed'),
    ], string="State", default='draft', tracking=True)
    progress_percentage = fields.Float(string="Progress (%)", compute="_compute_progress_percentage", store=True)
    description = fields.Text(string="Description")
    responsible_id = fields.Many2one("hr.employee", string="Responsible Person")

    @api.depends('target_value', 'current_value')
    def _compute_progress_percentage(self):
        for rec in recs if 'recs' in locals() else self:
            if rec.target_value and rec.target_value > 0:
                rec.progress_percentage = (rec.current_value / rec.target_value) * 100.0
            else:
                rec.progress_percentage = 0.0

    def action_activate(self):
        self.write({'state': 'active'})

    def action_achieve(self):
        self.write({'state': 'achieved'})

    def action_miss(self):
        self.write({'state': 'missed'})

    def action_draft(self):
        self.write({'state': 'draft'})
