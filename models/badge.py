from odoo import models, fields, api

class EsgBadge(models.Model):
    _name = "esg.badge"
    _description = "ESG Achievement Badge"
    _order = "name"

    name = fields.Char(string="Badge Name", required=True)
    description = fields.Text(string="Description")
    image = fields.Image(string="Badge Icon", max_width=128, max_height=128)
    rule_type = fields.Selection([
        ("xp_threshold", "XP Threshold"),
        ("challenge_count", "Challenges Completed"),
        ("csr_count", "CSR Activities Approved"),
    ], string="Award Trigger Rule", required=True, default="xp_threshold")
    rule_value = fields.Integer(string="Threshold Target Value", required=True, default=1)
    xp_reward = fields.Integer(string="XP Bonus Reward", default=0)
    active = fields.Boolean(string="Active", default=True)
    awarded_count = fields.Integer(string="Awarded Count", compute="_compute_awarded_count")

    def _compute_awarded_count(self):
        for rec in self:
            rec.awarded_count = self.env['esg.employee.badge'].search_count([('badge_id', '=', rec.id)])

    def check_unlock(self, employee):
        self.ensure_one()
        if self.rule_type == "xp_threshold":
            # Sum XP transaction amounts for this employee
            txs = self.env["esg.xp.transaction"].search([("employee_id", "=", employee.id)])
            actual = sum(txs.mapped("xp_amount"))
        elif self.rule_type == "challenge_count":
            # Count completed challenges
            actual = self.env["esg.challenge.participation"].search_count([
                ("employee_id", "=", employee.id),
                ("status", "=", "completed")
            ])
        else: # csr_count
            # Count approved CSR activities
            actual = self.env["esg.employee.participation"].search_count([
                ("employee_id", "=", employee.id),
                ("approval_status", "=", "approved")
            ])
        return actual >= self.rule_value

    def try_award_badge(self, employee):
        self.ensure_one()
        # Check if already awarded
        existing = self.env['esg.employee.badge'].search([
            ('employee_id', '=', employee.id),
            ('badge_id', '=', self.id)
        ])
        if existing:
            return False
            
        if self.check_unlock(employee):
            # Create link
            self.env['esg.employee.badge'].create({
                'employee_id': employee.id,
                'badge_id': self.id,
                'awarded_date': fields.Date.today(),
            })
            
            # Send message/chatter notification
            # If Odoo user is linked, post to employee record or user chatter
            message = f"🏆 Badge Unlocked: <strong>{self.name}</strong>! {self.description or ''}"
            employee.message_post(body=message, subtype_xmlid="mail.mt_note")
            
            # If xp_reward exists, create an XP transaction for it
            if self.xp_reward > 0:
                self.env['esg.xp.transaction'].create({
                    'employee_id': employee.id,
                    'xp_amount': self.xp_reward,
                    'transaction_type': 'badge',
                    'description': f"Unlocked badge: {self.name}",
                    'source_model': self._name,
                    'source_res_id': self.id,
                })
            return True
        return False


class EsgEmployeeBadge(models.Model):
    _name = "esg.employee.badge"
    _description = "Employee ESG Badges Awarded"
    _order = "awarded_date desc, id desc"

    employee_id = fields.Many2one("hr.employee", string="Employee", required=True, ondelete="cascade")
    badge_id = fields.Many2one("esg.badge", string="Badge", required=True, ondelete="cascade")
    awarded_date = fields.Date(string="Awarded Date", default=fields.Date.today, required=True)
    awarded_by_id = fields.Many2one("res.users", string="Awarded By", default=lambda self: self.env.user)

    _sql_constraints = [
        ('uniq_emp_badge', 'unique(employee_id, badge_id)', 'This employee already has this badge awarded!'),
    ]
