from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    esg_auto_emission_calc = fields.Boolean(
        string='Auto Emission Calculation',
        config_parameter='esg.auto_emission_calc',
        default=True,
        help="Enable automatic calculation and generation of CO₂e transactions on Purchase, Stock, and Fleet movements."
    )
    esg_auto_badge_award = fields.Boolean(
        string='Auto Badge Awards',
        config_parameter='esg.auto_badge_award',
        default=True,
        help="Enable automatic awarding of badges when thresholds (XP, challenge count, CSR count) are reached."
    )
    esg_weight_environmental = fields.Float(
        string='Environmental Weight',
        config_parameter='esg.weight_environmental',
        default=0.40,
        help="Weight of Environmental pillar in Total ESG Score (0.0 to 1.0)."
    )
    esg_weight_social = fields.Float(
        string='Social Weight',
        config_parameter='esg.weight_social',
        default=0.30,
        help="Weight of Social pillar in Total ESG Score (0.0 to 1.0)."
    )
    esg_weight_governance = fields.Float(
        string='Governance Weight',
        config_parameter='esg.weight_governance',
        default=0.30,
        help="Weight of Governance pillar in Total ESG Score (0.0 to 1.0)."
    )
    esg_evidence_required_default = fields.Boolean(
        string='Require Evidence by Default',
        config_parameter='esg.evidence_required_default',
        default=False,
        help="Make proof/evidence attachment mandatory by default when creating new CSR activities."
    )
