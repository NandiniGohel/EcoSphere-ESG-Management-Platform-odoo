from odoo import models, fields

class EsgCategory(models.Model):
    _name = "esg.category"
    _description = "ESG Activity and Challenge Category"
    _order = "name"

    name = fields.Char(string="Category Name", required=True, translate=True)
    type = fields.Selection([
        ('csr', 'CSR Activity'),
        ('challenge', 'Challenge'),
    ], string="Category Type", required=True, default='csr')
    description = fields.Text(string="Description")
    color = fields.Integer(string="Color Index", default=0)
    active = fields.Boolean(string="Active", default=True)
