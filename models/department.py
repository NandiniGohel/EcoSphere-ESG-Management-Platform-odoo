from odoo import models, fields, api

class EsgDepartment(models.Model):
    _inherit = 'hr.department'

    esg_head_id = fields.Many2one('hr.employee', string='ESG Owner')
    esg_status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ], default='active', string='ESG Status')
    environmental_score = fields.Float(
        compute='_compute_esg_scores', store=True, string='Environmental Score'
    )
    social_score = fields.Float(
        compute='_compute_esg_scores', store=True, string='Social Score'
    )
    governance_score = fields.Float(
        compute='_compute_esg_scores', store=True, string='Governance Score'
    )
    total_score = fields.Float(
        compute='_compute_esg_scores', store=True, string='Total ESG Score'
    )
    carbon_budget = fields.Float(string='Carbon Budget (tCO₂e)')
    carbon_used = fields.Float(
        compute='_compute_carbon_used', store=True, string='Carbon Used (tCO₂e)'
    )
    carbon_remaining = fields.Float(
        compute='_compute_carbon_used', store=True, string='Carbon Remaining (tCO₂e)'
    )

    @api.depends('carbon_budget')
    def _compute_carbon_used(self):
        for dept in self:
            transactions = self.env['esg.carbon.transaction'].search([
                ('department_id', '=', dept.id)
            ])
            used = sum(transactions.mapped('co2e_tonnes'))
            dept.carbon_used = used
            dept.carbon_remaining = (dept.carbon_budget or 0.0) - used

    def _compute_environmental_score(self):
        """Compute environmental score based on carbon transactions vs goals."""
        self.ensure_one()
        goals = self.env['esg.environmental.goal'].search([
            ('department_id', '=', self.id),
            ('state', '=', 'active'),
        ])
        if not goals:
            return 0.0
        # Score = average progress across all active goals (capped at 100)
        scores = []
        for goal in goals:
            if goal.target_value and goal.target_value > 0:
                progress = (goal.current_value / goal.target_value) * 100.0
                scores.append(min(progress, 100.0))
        return sum(scores) / len(scores) if scores else 0.0

    def _compute_social_score(self):
        """Compute social score based on CSR and challenge participation."""
        self.ensure_one()
        # Count approved CSR participations from this dept
        employees = self.member_ids
        if not employees:
            return 0.0
        approved = self.env['esg.employee.participation'].search_count([
            ('employee_id', 'in', employees.ids),
            ('approval_status', '=', 'approved'),
        ])
        completed_challenges = self.env['esg.challenge.participation'].search_count([
            ('employee_id', 'in', employees.ids),
            ('status', '=', 'completed'),
        ])
        # Simple formula: (approved CSR + completed challenges) / employee_count * 10, capped at 100
        employee_count = max(len(employees), 1)
        raw_score = ((approved + completed_challenges) / employee_count) * 10.0
        return min(raw_score, 100.0)

    def _compute_governance_score(self):
        """Compute governance score based on policy acknowledgements and open issues."""
        self.ensure_one()
        employees = self.member_ids
        if not employees:
            return 0.0
        # Acknowledgement rate
        active_policies = self.env['esg.policy'].search_count([('state', '=', 'active')])
        if active_policies == 0:
            return 100.0
        acknowledged = self.env['esg.policy.acknowledgement'].search_count([
            ('employee_id', 'in', employees.ids),
            ('state', '=', 'acknowledged'),
        ])
        expected = active_policies * max(len(employees), 1)
        ack_rate = (acknowledged / expected) * 100.0 if expected > 0 else 0.0

        # Penalty for open compliance issues
        open_issues = self.env['esg.compliance.issue'].search_count([
            ('department_id', '=', self.id),
            ('status', 'in', ['open', 'overdue']),
        ])
        penalty = min(open_issues * 5.0, 50.0)
        return max(min(ack_rate - penalty, 100.0), 0.0)

    @api.depends('member_ids', 'carbon_budget')
    def _compute_esg_scores(self):
        weights = self.env['ir.config_parameter'].sudo()
        e_w = float(weights.get_param('esg.weight_environmental', 0.40))
        s_w = float(weights.get_param('esg.weight_social', 0.30))
        g_w = float(weights.get_param('esg.weight_governance', 0.30))
        for dept in self:
            dept.environmental_score = dept._compute_environmental_score()
            dept.social_score = dept._compute_social_score()
            dept.governance_score = dept._compute_governance_score()
            dept.total_score = (
                dept.environmental_score * e_w
                + dept.social_score * s_w
                + dept.governance_score * g_w
            )

    @api.model
    def _cron_recompute_all_scores(self):
        departments = self.search([])
        for dept in departments:
            dept._compute_esg_scores()
