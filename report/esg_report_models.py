from odoo import api, models
from datetime import date

class ReportEsgSummary(models.AbstractModel):
    _name = 'report.esg_management.report_esg_summary_template'
    _description = 'ESG Summary Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data or {}
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        dept_ids = data.get('department_ids', [])

        if dept_ids:
            departments = self.env['hr.department'].browse(dept_ids)
        else:
            departments = self.env['hr.department'].search([])

        dept_data = []
        for dept in departments:
            carbon_domain = [('department_id', '=', dept.id)]
            if date_from:
                carbon_domain.append(('date', '>=', date_from))
            if date_to:
                carbon_domain.append(('date', '<=', date_to))

            transactions = self.env['esg.carbon.transaction'].search(carbon_domain)
            total_co2 = sum(transactions.mapped('co2e_tonnes'))

            dept_data.append({
                'name': dept.name,
                'total_score': dept.total_score,
                'environmental_score': dept.environmental_score,
                'social_score': dept.social_score,
                'governance_score': dept.governance_score,
                'total_co2_tonnes': total_co2,
                'employee_count': len(dept.member_ids),
            })

        return {
            'doc_ids': docids,
            'doc_model': 'esg.report.builder',
            'docs': dept_data,
            'data': data,
            'company': self.env.company,
            'report_date': str(date.today()),
        }


class ReportEsgEnvironmental(models.AbstractModel):
    _name = 'report.esg_management.report_esg_environmental_template'
    _description = 'ESG Environmental Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data or {}
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        dept_ids = data.get('department_ids', [])

        domain = []
        if dept_ids:
            domain.append(('department_id', 'in', dept_ids))
        if date_from:
            domain.append(('date', '>=', date_from))
        if date_to:
            domain.append(('date', '<=', date_to))

        transactions = self.env['esg.carbon.transaction'].search(domain)
        goals = self.env['esg.environmental.goal'].search(
            [('department_id', 'in', dept_ids)] if dept_ids else []
        )

        # Summarize by scope
        scope_summary = {
            '1': 0.0,
            '2': 0.0,
            '3': 0.0
        }
        for tx in transactions:
            if tx.scope in scope_summary:
                scope_summary[tx.scope] += tx.co2e_tonnes

        return {
            'doc_ids': docids,
            'doc_model': 'esg.report.builder',
            'transactions': transactions,
            'goals': goals,
            'scope_summary': scope_summary,
            'data': data,
            'company': self.env.company,
            'report_date': str(date.today()),
        }


class ReportEsgSocial(models.AbstractModel):
    _name = 'report.esg_management.report_esg_social_template'
    _description = 'ESG Social Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data or {}
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        dept_ids = data.get('department_ids', [])

        csr_domain = []
        challenge_domain = []
        if dept_ids:
            csr_domain.append(('department_id', 'in', dept_ids))
            challenge_domain.append(('department_id', 'in', dept_ids))
        if date_from:
            csr_domain.append(('activity_id.activity_date', '>=', date_from))
            challenge_domain.append(('enrollment_date', '>=', date_from))
        if date_to:
            csr_domain.append(('activity_id.activity_date', '<=', date_to))
            challenge_domain.append(('enrollment_date', '<=', date_to))

        participations = self.env['esg.employee.participation'].search(csr_domain)
        challenge_participations = self.env['esg.challenge.participation'].search(challenge_domain)

        # Leaderboard (top employees by XP in the system/period)
        xp_domain = []
        if date_from:
            xp_domain.append(('date', '>=', date_from))
        if date_to:
            xp_domain.append(('date', '<=', date_to))
        
        # We group by employee and sum the XP
        xp_transactions = self.env['esg.xp.transaction'].search(xp_domain)
        employee_xp = {}
        for tx in xp_transactions:
            employee_xp[tx.employee_id] = employee_xp.get(tx.employee_id, 0) + tx.xp_amount
        
        # Sort and take top 10
        top_employees = sorted(employee_xp.items(), key=lambda item: item[1], reverse=True)[:10]

        return {
            'doc_ids': docids,
            'doc_model': 'esg.report.builder',
            'participations': participations,
            'challenge_participations': challenge_participations,
            'top_employees': [{'employee': k, 'xp': v} for k, v in top_employees],
            'data': data,
            'company': self.env.company,
            'report_date': str(date.today()),
        }


class ReportEsgGovernance(models.AbstractModel):
    _name = 'report.esg_management.report_esg_governance_template'
    _description = 'ESG Governance Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data or {}
        dept_ids = data.get('department_ids', [])

        policies = self.env['esg.policy'].search([('state', '=', 'active')])
        p_acks = self.env['esg.policy.acknowledgement'].search([])
        
        # Policy completion rate
        policy_completion = []
        for pol in policies:
            # Expected acks
            depts = pol.department_ids or self.env['hr.department'].search([])
            employees = self.env['hr.employee'].search([('department_id', 'in', depts.ids)])
            total_expected = len(employees)
            
            acks = p_acks.filtered(lambda r: r.policy_id == pol and r.state == 'acknowledged' and r.employee_id in employees)
            total_acks = len(acks)
            
            rate = (total_acks / total_expected * 100.0) if total_expected > 0 else 100.0
            policy_completion.append({
                'policy': pol,
                'expected': total_expected,
                'acks': total_acks,
                'rate': rate
            })

        issue_domain = []
        audit_domain = []
        if dept_ids:
            issue_domain.append(('department_id', 'in', dept_ids))
            audit_domain.append(('department_ids', 'in', dept_ids))

        issues = self.env['esg.compliance.issue'].search(issue_domain)
        audits = self.env['esg.audit'].search(audit_domain)

        return {
            'doc_ids': docids,
            'doc_model': 'esg.report.builder',
            'policy_completion': policy_completion,
            'issues': issues,
            'audits': audits,
            'data': data,
            'company': self.env.company,
            'report_date': str(date.today()),
        }
