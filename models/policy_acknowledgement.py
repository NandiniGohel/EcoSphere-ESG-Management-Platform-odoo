from odoo import models, fields, api

class EsgPolicyAcknowledgement(models.Model):
    _name = "esg.policy.acknowledgement"
    _description = "ESG Policy Acknowledgement"
    _order = "acknowledged_date desc, id desc"

    policy_id = fields.Many2one("esg.policy", string="Policy", required=True, ondelete="cascade")
    employee_id = fields.Many2one("hr.employee", string="Employee", required=True, ondelete="cascade")
    state = fields.Selection([
        ('pending', 'Pending Acknowledgement'),
        ('acknowledged', 'Acknowledged'),
    ], string="Status", default='pending', required=True)
    acknowledged_date = fields.Datetime(string="Acknowledgement Date")
    ip_address = fields.Char(string="IP Address / Method")

    _sql_constraints = [
        ('uniq_policy_employee', 'unique(policy_id, employee_id)', 'This employee acknowledgement record already exists!'),
    ]

    def action_acknowledge(self):
        for rec in self:
            if rec.state == 'acknowledged':
                continue
            rec.write({
                'state': 'acknowledged',
                'acknowledged_date': fields.Datetime.now(),
                # IP address can be captured in a web controller if done via portal, otherwise set local/stub
                'ip_address': 'Odoo Local System'
            })
            
            # Post chatter on policy
            rec.policy_id.message_post(body=f"✍️ Policy acknowledged by employee {rec.employee_id.name}.")
