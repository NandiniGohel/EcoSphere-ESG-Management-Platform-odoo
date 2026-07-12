from odoo import models, fields, api

class EsgDepartmentScore(models.Model):
    _name = "esg.department.score"
    _description = "Department ESG Score History"
    _order = "date desc, department_id"

    department_id = fields.Many2one("hr.department", string="Department", required=True, ondelete="cascade")
    date = fields.Date(string="Date", required=True, default=fields.Date.today)
    environmental_score = fields.Float(string="Environmental Score")
    social_score = fields.Float(string="Social Score")
    governance_score = fields.Float(string="Governance Score")
    total_score = fields.Float(string="Total Score")
    period = fields.Selection([
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ], string="Snapshot Period", default='daily', required=True)

    _sql_constraints = [
        ('uniq_dept_date_period', 'unique(department_id, date, period)', 'A snapshot for this department, date, and period already exists!'),
    ]

    @api.model
    def _cron_snapshot(self):
        # Trigger recompute of department scores first to make sure they are up-to-date
        departments = self.env['hr.department'].search([])
        for dept in departments:
            dept._compute_esg_scores()
            
        today_date = fields.Date.today()
        for dept in departments:
            # Check if daily snapshot exists for today
            existing = self.search([
                ('department_id', '=', dept.id),
                ('date', '=', today_date),
                ('period', '=', 'daily')
            ])
            vals = {
                'department_id': dept.id,
                'date': today_date,
                'environmental_score': dept.environmental_score,
                'social_score': dept.social_score,
                'governance_score': dept.governance_score,
                'total_score': dept.total_score,
                'period': 'daily'
            }
            if existing:
                existing.write(vals)
            else:
                self.create(vals)
