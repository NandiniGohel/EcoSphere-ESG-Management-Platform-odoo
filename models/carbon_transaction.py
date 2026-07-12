from odoo import models, fields, api

class EsgCarbonTransaction(models.Model):
    _name = 'esg.carbon.transaction'
    _description = 'ESG Carbon Transaction'
    _inherit = ['mail.thread']
    _order = 'date desc, id desc'

    name = fields.Char(string='Reference', required=True, copy=False,
                       readonly=True, default=lambda self: self.env['ir.sequence'].next_by_code('esg.carbon.transaction') or '/')
    department_id = fields.Many2one('hr.department', string='Department', required=True, tracking=True)
    emission_factor_id = fields.Many2one('esg.emission.factor', string='Emission Factor', required=True, tracking=True)
    date = fields.Date(string='Date', required=True, default=fields.Date.today)
    quantity = fields.Float(string='Quantity', required=True, digits=(16, 4), tracking=True)
    unit = fields.Char(related='emission_factor_id.unit', string='Unit', readonly=True)
    scope = fields.Selection(related='emission_factor_id.scope', string='Scope', readonly=True, store=True)
    co2e_kg = fields.Float(string='CO₂e (kg)', compute='_compute_co2e', store=True, digits=(16, 4))
    co2e_tonnes = fields.Float(string='CO₂e (tonnes)', compute='_compute_co2e', store=True, digits=(16, 6))
    source_model = fields.Char(string='Source Model')
    source_res_id = fields.Integer(string='Source Record ID')
    entry_type = fields.Selection([
        ('manual', 'Manual Entry'),
        ('auto', 'Auto-calculated'),
        ('import', 'Imported'),
    ], default='manual', string='Entry Type', tracking=True)
    notes = fields.Text(string='Notes')
    employee_id = fields.Many2one('hr.employee', string='Responsible Employee')

    @api.depends('quantity', 'emission_factor_id.factor_value')
    def _compute_co2e(self):
        for rec in self:
            factor = rec.emission_factor_id.factor_value or 0.0
            rec.co2e_kg = rec.quantity * factor
            rec.co2e_tonnes = rec.co2e_kg / 1000.0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code('esg.carbon.transaction') or '/'
        return super(EsgCarbonTransaction, self).create(vals_list)

    @api.model
    def create_from_source(self, source_record, quantity, emission_factor=None):
        """Called from purchase/stock/expense/fleet hooks when auto-calc is enabled."""
        if not self.env['ir.config_parameter'].sudo().get_param('esg.auto_emission_calc'):
            return False
        factor = emission_factor or (getattr(source_record, 'emission_factor_id', None))
        if not factor:
            return False
        dept_id = False
        if hasattr(source_record, 'department_id') and source_record.department_id:
            dept_id = source_record.department_id.id
        elif hasattr(source_record, 'employee_id') and source_record.employee_id and source_record.employee_id.department_id:
            dept_id = source_record.employee_id.department_id.id
        
        # Fallback to checking the creator or editor's department
        if not dept_id:
            user = False
            if hasattr(source_record, 'write_uid') and source_record.write_uid:
                user = source_record.write_uid
            elif hasattr(source_record, 'create_uid') and source_record.create_uid:
                user = source_record.create_uid
            
            # Special check for purchase order line which points to order_id
            if not user and hasattr(source_record, 'order_id') and source_record.order_id:
                user = source_record.order_id.user_id or source_record.order_id.create_uid
                
            if user:
                employee = self.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
                if employee and employee.department_id:
                    dept_id = employee.department_id.id

        if not dept_id:
            return False
        return self.create({
            'department_id': dept_id,
            'emission_factor_id': factor.id,
            'source_model': source_record._name,
            'source_res_id': source_record.id,
            'quantity': quantity,
            'entry_type': 'auto',
            'date': fields.Date.today(),
        })

    _sql_constraints = [
        ('positive_quantity', 'CHECK(quantity >= 0)', 'Quantity must be non-negative.'),
    ]
