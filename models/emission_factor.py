from odoo import models, fields

class EsgEmissionFactor(models.Model):
    _name = "esg.emission.factor"
    _description = "ESG Emission Factor"
    _order = "name"

    name = fields.Char(string="Factor Name", required=True)
    factor_value = fields.Float(string="Factor Value (kg CO₂e/unit)", required=True, digits=(16, 6))
    unit = fields.Char(string="Unit", required=True, help="e.g. kWh, Litre, km, kg")
    scope = fields.Selection([
        ('1', 'Scope 1 - Direct Emissions'),
        ('2', 'Scope 2 - Indirect Emissions (Electricity/Heat)'),
        ('3', 'Scope 3 - Other Indirect Emissions (Value Chain)'),
    ], string="Scope", required=True, default='1')
    source = fields.Char(string="Source/Standard", help="e.g. GHG Protocol, EPA 2024, DEFRA")
    valid_from = fields.Date(string="Valid From")
    valid_to = fields.Date(string="Valid To")
    active = fields.Boolean(string="Active", default=True)
    notes = fields.Text(string="Notes")
