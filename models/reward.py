from odoo import models, fields, api, _
from odoo.exceptions import UserError

class EsgReward(models.Model):
    _name = "esg.reward"
    _description = "ESG Gamification Reward"
    _order = "xp_cost, name"

    name = fields.Char(string="Reward Title", required=True)
    description = fields.Text(string="Description")
    image = fields.Image(string="Image", max_width=128, max_height=128)
    xp_cost = fields.Integer(string="XP Cost", required=True, default=100)
    stock_quantity = fields.Integer(string="Stock Quantity", default=-1, help="Use -1 for unlimited stock")
    redeemed_count = fields.Integer(string="Redeemed Count", compute="_compute_redeemed_count", store=True)
    available = fields.Boolean(string="Available", compute="_compute_available")
    active = fields.Boolean(string="Active", default=True)
    category = fields.Selection([
        ('physical', 'Physical Item'),
        ('voucher', 'Voucher / Gift Card'),
        ('experience', 'Experience / Time Off'),
        ('donation', 'Charitable Donation'),
    ], string="Category", required=True, default='physical')

    redemption_ids = fields.One2many("esg.reward.redemption", "reward_id", string="Redemptions")

    @api.depends('redemption_ids.state')
    def _compute_redeemed_count(self):
        for rec in self:
            rec.redeemed_count = len(rec.redemption_ids.filtered(lambda r: r.state in ('approved', 'delivered')))

    @api.depends('stock_quantity', 'redeemed_count')
    def _compute_available(self):
        for rec in self:
            if rec.stock_quantity == -1:
                rec.available = True
            else:
                rec.available = rec.stock_quantity > rec.redeemed_count

class EsgRewardRedemption(models.Model):
    _name = "esg.reward.redemption"
    _description = "ESG Reward Redemption Request"
    _inherit = ['mail.thread']
    _order = "redemption_date desc, id desc"

    employee_id = fields.Many2one("hr.employee", string="Employee", required=True, tracking=True)
    reward_id = fields.Many2one("esg.reward", string="Requested Reward", required=True, tracking=True)
    redemption_date = fields.Datetime(string="Request Date", default=fields.Datetime.now, required=True)
    state = fields.Selection([
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('delivered', 'Delivered'),
    ], string="Status", default='pending', tracking=True)
    notes = fields.Text(string="Notes")

    def action_approve(self):
        for rec in self:
            if rec.state != 'pending':
                continue
                
            # Check availability
            reward = rec.reward_id
            if not reward.available:
                raise UserError(_("The reward '%s' is out of stock.") % reward.name)
                
            # Check employee XP balance
            total_xp = rec.employee_id.total_xp
            if total_xp < reward.xp_cost:
                raise UserError(_("Employee '%s' has insufficient XP (%s) to redeem '%s' (costs %s XP).") % 
                                (rec.employee_id.name, total_xp, reward.name, reward.xp_cost))
            
            # Deduct XP by creating a negative transaction
            self.env['esg.xp.transaction'].create({
                'employee_id': rec.employee_id.id,
                'xp_amount': -reward.xp_cost,
                'transaction_type': 'redemption',
                'description': f"Redeemed reward: {reward.name}",
                'source_model': rec._name,
                'source_res_id': rec.id,
            })
            
            rec.write({'state': 'approved'})
            
            # Post success chatter
            rec.message_post(body=f"✅ Redemption request approved. {reward.xp_cost} XP deducted.")
            rec.employee_id.message_post(body=f"🎁 Reward Redeemed: <strong>{reward.name}</strong> for {reward.xp_cost} XP.")

    def action_reject(self):
        for rec in self:
            if rec.state != 'pending':
                continue
            rec.write({'state': 'rejected'})
            rec.message_post(body="❌ Redemption request rejected.")

    def action_deliver(self):
        for rec in self:
            if rec.state != 'approved':
                continue
            rec.write({'state': 'delivered'})
            rec.message_post(body="📦 Reward marked as delivered.")
