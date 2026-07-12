import io
import csv
import base64
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class EsgReportBuilder(models.TransientModel):
    _name = "esg.report.builder"
    _description = "ESG Report Builder Wizard"

    date_from = fields.Date(string="Date From", required=True)
    date_to = fields.Date(string="Date To", required=True)
    department_ids = fields.Many2many("hr.department", string="Departments")
    module_type = fields.Selection([
        ("all", "All Modules"),
        ("environmental", "Environmental"),
        ("social", "Social"),
        ("governance", "Governance"),
    ], default="all", string="Module Filter")
    employee_ids = fields.Many2many("hr.employee", string="Employees")
    challenge_ids = fields.Many2many("esg.challenge", string="Challenges")
    category_ids = fields.Many2many("esg.category", string="Categories")
    
    export_format = fields.Selection([
        ("pdf", "PDF Report"),
        ("csv", "CSV"),
        ("xlsx", "Excel (XLSX)"),
    ], default="pdf", string="Export Format", required=True)
    
    report_type = fields.Selection([
        ("summary", "Summary Report"),
        ("environmental", "Environmental Detail"),
        ("social", "Social Detail"),
        ("governance", "Governance Detail"),
    ], default="summary", string="Report Type", required=True)

    # For binary file download pattern
    file_data = fields.Binary(string="Generated File", readonly=True)
    file_name = fields.Char(string="File Name", readonly=True)
    state = fields.Selection([
        ("choose", "Choose Filters"),
        ("get", "Download File"),
    ], default="choose")

    def _prepare_report_data(self):
        self.ensure_one()
        return {
            'date_from': str(self.date_from),
            'date_to': str(self.date_to),
            'department_ids': self.department_ids.ids,
            'module_type': self.module_type,
            'employee_ids': self.employee_ids.ids,
            'challenge_ids': self.challenge_ids.ids,
            'category_ids': self.category_ids.ids,
            'report_type': self.report_type,
        }

    def action_generate_report(self):
        self.ensure_one()
        if self.date_from > self.date_to:
            raise UserError(_("Start Date cannot be after End Date."))

        if self.export_format == 'pdf':
            report_ref = 'esg_management.action_report_esg_summary'
            if self.report_type == 'environmental':
                report_ref = 'esg_management.action_report_esg_environmental'
            elif self.report_type == 'social':
                report_ref = 'esg_management.action_report_esg_social'
            elif self.report_type == 'governance':
                report_ref = 'esg_management.action_report_esg_governance'
            
            return self.env.ref(report_ref).report_action(self, data=self._prepare_report_data())

        elif self.export_format in ('csv', 'xlsx'):
            return self.action_export_file()

    def action_export_file(self):
        self.ensure_one()
        output = io.StringIO()
        writer = csv.writer(output, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        # Write header
        writer.writerow(["ESG Report", self.report_type.upper(), f"Period: {self.date_from} to {self.date_to}"])
        writer.writerow([])

        # Filter by department
        depts = self.department_ids or self.env['hr.department'].search([])

        if self.report_type == 'summary' or self.module_type == 'all':
            writer.writerow(["Department", "Environmental Score", "Social Score", "Governance Score", "Total Score", "Carbon Used (tCO2e)"])
            for dept in depts:
                # Calculate carbon used in period
                carbon_domain = [('department_id', '=', dept.id), ('date', '>=', self.date_from), ('date', '<=', self.date_to)]
                if self.category_ids:
                    carbon_domain.append(('emission_factor_id', 'in', self.category_ids.ids)) # or filter appropriately
                
                txs = self.env['esg.carbon.transaction'].search(carbon_domain)
                co2_tonnes = sum(txs.mapped('co2e_tonnes'))
                
                writer.writerow([
                    dept.name,
                    round(dept.environmental_score, 2),
                    round(dept.social_score, 2),
                    round(dept.governance_score, 2),
                    round(dept.total_score, 2),
                    round(co2_tonnes, 4)
                ])

        elif self.report_type == 'environmental':
            writer.writerow(["Date", "Department", "Reference", "Emission Factor", "Scope", "Quantity", "Unit", "CO2e (kg)", "CO2e (tonnes)", "Type"])
            domain = [('date', '>=', self.date_from), ('date', '<=', self.date_to)]
            if self.department_ids:
                domain.append(('department_id', 'in', self.department_ids.ids))
            if self.employee_ids:
                domain.append(('employee_id', 'in', self.employee_ids.ids))
            
            txs = self.env['esg.carbon.transaction'].search(domain)
            for tx in txs:
                writer.writerow([
                    tx.date,
                    tx.department_id.name,
                    tx.name,
                    tx.emission_factor_id.name,
                    tx.scope,
                    tx.quantity,
                    tx.unit,
                    round(tx.co2e_kg, 2),
                    round(tx.co2e_tonnes, 4),
                    tx.entry_type
                ])

        elif self.report_type == 'social':
            writer.writerow(["Type", "Activity/Challenge Name", "Employee", "Department", "Status/Date", "XP Earned"])
            
            # CSR Activity participations
            csr_domain = [('activity_id.activity_date', '>=', self.date_from), ('activity_id.activity_date', '<=', self.date_to)]
            if self.department_ids:
                csr_domain.append(('department_id', 'in', self.department_ids.ids))
            if self.employee_ids:
                csr_domain.append(('employee_id', 'in', self.employee_ids.ids))
            if self.category_ids:
                csr_domain.append(('activity_id.category_id', 'in', self.category_ids.ids))

            participations = self.env['esg.employee.participation'].search(csr_domain)
            for p in participations:
                writer.writerow([
                    "CSR Activity",
                    p.activity_id.name,
                    p.employee_id.name,
                    p.department_id.name,
                    p.approval_status,
                    p.activity_id.xp_reward if p.approval_status == 'approved' else 0
                ])

            # Challenges
            chal_domain = [('enrollment_date', '>=', self.date_from), ('enrollment_date', '<=', self.date_to)]
            if self.department_ids:
                chal_domain.append(('department_id', 'in', self.department_ids.ids))
            if self.employee_ids:
                chal_domain.append(('employee_id', 'in', self.employee_ids.ids))
            if self.challenge_ids:
                chal_domain.append(('challenge_id', 'in', self.challenge_ids.ids))

            c_participations = self.env['esg.challenge.participation'].search(chal_domain)
            for cp in c_participations:
                writer.writerow([
                    "Challenge",
                    cp.challenge_id.name,
                    cp.employee_id.name,
                    cp.department_id.name,
                    cp.status,
                    cp.challenge_id.xp_reward if cp.status == 'completed' else 0
                ])

        elif self.report_type == 'governance':
            writer.writerow(["Type", "Name/Title", "Details/Department", "Date/Status", "Severity/Responsible"])
            
            # Policy Acknowledger
            pol_domain = []
            if self.employee_ids:
                pol_domain.append(('employee_id', 'in', self.employee_ids.ids))
            
            pols = self.env['esg.policy.acknowledgement'].search(pol_domain)
            for pa in pols:
                writer.writerow([
                    "Policy Acknowledgement",
                    pa.policy_id.name,
                    pa.employee_id.name,
                    pa.state,
                    pa.acknowledged_date or ""
                ])

            # Compliance issues
            comp_domain = []
            if self.department_ids:
                comp_domain.append(('department_id', 'in', self.department_ids.ids))
            if self.employee_ids:
                comp_domain.append(('responsible_id', 'in', self.employee_ids.ids))
            
            issues = self.env['esg.compliance.issue'].search(comp_domain)
            for issue in issues:
                writer.writerow([
                    "Compliance Issue",
                    issue.name,
                    issue.department_id.name,
                    issue.status,
                    f"{issue.severity} / {issue.responsible_id.name or 'Unassigned'}"
                ])

        # Generate File
        file_val = base64.b64encode(output.getvalue().encode('utf-8'))
        ext = self.export_format
        filename = f"esg_{self.report_type}_report_{self.date_from}_to_{self.date_to}.{ext}"

        self.write({
            'file_data': file_val,
            'file_name': filename,
            'state': 'get',
        })
        
        output.close()
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
        }
