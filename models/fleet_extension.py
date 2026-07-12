from odoo import models, fields, api

class FleetVehicleLogServices(models.Model):
    _inherit = 'fleet.vehicle.log.services'

    liter = fields.Float(string='Liters', help='Liters of fuel')
    emission_factor_id = fields.Many2one('esg.emission.factor', string='Emission Factor')
    employee_id = fields.Many2one('hr.employee', string='Driver Employee', compute='_compute_employee_id', store=True)

    @api.depends('purchaser_id')
    def _compute_employee_id(self):
        for rec in self:
            if rec.purchaser_id:
                employee = self.env['hr.employee'].search([
                    '|',
                    ('work_contact_id', '=', rec.purchaser_id.id),
                    ('user_id.partner_id', '=', rec.purchaser_id.id)
                ], limit=1)
                rec.employee_id = employee
            else:
                rec.employee_id = False

    @api.model_create_multi
    def create(self, vals_list):
        records = super(FleetVehicleLogServices, self).create(vals_list)
        if self.env['ir.config_parameter'].sudo().get_param('esg.auto_emission_calc', True):
            for rec in records:
                if rec.emission_factor_id and rec.liter > 0:
                    self.env['esg.carbon.transaction'].create_from_source(
                        rec, 
                        rec.liter, 
                        rec.emission_factor_id
                    )
        return records

    def write(self, vals):
        res = super(FleetVehicleLogServices, self).write(vals)
        if self.env['ir.config_parameter'].sudo().get_param('esg.auto_emission_calc', True):
            if 'liter' in vals or 'emission_factor_id' in vals:
                for rec in self:
                    if rec.emission_factor_id and rec.liter > 0:
                        # Check if transaction already exists for this fuel log to avoid duplicates, or update it
                        existing = self.env['esg.carbon.transaction'].search([
                            ('source_model', '=', self._name),
                            ('source_res_id', '=', rec.id)
                        ])
                        if existing:
                            existing.write({
                                'quantity': rec.liter,
                                'emission_factor_id': rec.emission_factor_id.id,
                            })
                        else:
                            self.env['esg.carbon.transaction'].create_from_source(
                                rec, 
                                rec.liter, 
                                rec.emission_factor_id
                            )
        return res
